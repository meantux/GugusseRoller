#!/usr/bin/env python3
"""
RAW Camera Viewer — Standalone tool for GugusseRoller / RPi HQ Camera
Live preview + histogram + 12-bit CSI2P unpacking explorer

Usage: python3 raw_viewer.py
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QGroupBox, QGridLayout, QSlider, QCheckBox,
    QFrame, QSizePolicy, QPushButton, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QFontDatabase
import pyqtgraph as pg

# ── picamera2 import (graceful fallback for dev on non-Pi) ──────────────────
try:
    from picamera2 import Picamera2
    from libcamera import Transform
    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False
    print("WARNING: picamera2 not found — running in SIMULATION mode")

# ═══════════════════════════════════════════════════════════════════════════════
# 12-bit CSI2 Packed (SBGGR12_CSI2P) unpacker
# The IMX477 packs 2 pixels into 3 bytes:
#
#   Standard (MIPI CSI-2):
#     Byte0 = P0[11:4]   (MSByte of pixel 0, upper 8 bits)
#     Byte1 = P1[11:4]   (MSByte of pixel 1, upper 8 bits)
#     Byte2 = P1[3:0] P0[3:0]  (low nibbles, P1 in high, P0 in low)
#
#   We expose full control over:
#     - which nibble of byte2 goes to which pixel (nibble_swap)
#     - whether the 8-bit MSB comes first or last (msb_first)
#     - whether the result is left- or right-aligned in 16 bits (align)
#     - whether the pixel pair order is swapped (pixel_swap)
# ═══════════════════════════════════════════════════════════════════════════════

UNPACK_MODES = {
    # name: (description, lambda that unpacks flat uint8 array → uint16 array)
    "Standard CSI2P\n(P0hi=B0, P1hi=B1, lo=B2[3:0]/B2[7:4])": "standard",
    "Swapped nibbles\n(P0hi=B0, P1hi=B1, lo=B2[7:4]/B2[3:0])": "nibble_swap",
    "Byte order flip\n(P0hi=B1, P1hi=B0, lo=B2[3:0]/B2[7:4])": "byte_swap",
    "Byte+nibble flip\n(P0hi=B1, P1hi=B0, lo=B2[7:4]/B2[3:0])": "byte_nibble_swap",
    "LSB-first B0\n(P0=B0[3:0]<<8|B2, etc.)": "lsb_b0",
    "Big-endian 16b\n(swap bytes of each uint16)": "big_endian",
    "Pixel pair swap\n(standard but P0↔P1)": "pixel_swap",
    "Pixel+nibble swap\n(swapped pair + swapped nibbles)": "pixel_nibble_swap",
}

def unpack_12bit(raw_bytes: np.ndarray, mode: str, align: str = "left") -> np.ndarray:
    """
    Unpack 12-bit packed CSI2 data to 16-bit.
    raw_bytes: flat uint8 array (length must be multiple of 3)
    mode: one of the UNPACK_MODES values
    align: 'left' (shift <<4 → use full 16-bit range) or 'right' (keep as 12-bit in 16-bit)
    Returns: uint16 array of pixel values
    """
    # Ensure we have complete triplets
    n_triplets = len(raw_bytes) // 3
    b = raw_bytes[:n_triplets * 3].reshape(-1, 3).astype(np.uint32)

    b0, b1, b2 = b[:, 0], b[:, 1], b[:, 2]

    if mode == "standard":
        p0 = (b0 << 4) | (b2 & 0x0F)
        p1 = (b1 << 4) | ((b2 >> 4) & 0x0F)

    elif mode == "nibble_swap":
        p0 = (b0 << 4) | ((b2 >> 4) & 0x0F)
        p1 = (b1 << 4) | (b2 & 0x0F)

    elif mode == "byte_swap":
        p0 = (b1 << 4) | (b2 & 0x0F)
        p1 = (b0 << 4) | ((b2 >> 4) & 0x0F)

    elif mode == "byte_nibble_swap":
        p0 = (b1 << 4) | ((b2 >> 4) & 0x0F)
        p1 = (b0 << 4) | (b2 & 0x0F)

    elif mode == "lsb_b0":
        # Treat B2 as the high byte, low nibble of B0/B1 as LSBs
        p0 = ((b2 & 0x0F) << 8) | b0
        p1 = (((b2 >> 4) & 0x0F) << 8) | b1

    elif mode == "big_endian":
        # Standard unpack then byte-swap each 16-bit word
        p0_raw = (b0 << 4) | (b2 & 0x0F)
        p1_raw = (b1 << 4) | ((b2 >> 4) & 0x0F)
        p0 = ((p0_raw & 0xFF) << 8) | ((p0_raw >> 8) & 0xFF)
        p1 = ((p1_raw & 0xFF) << 8) | ((p1_raw >> 8) & 0xFF)

    elif mode == "pixel_swap":
        p1 = (b0 << 4) | (b2 & 0x0F)
        p0 = (b1 << 4) | ((b2 >> 4) & 0x0F)

    elif mode == "pixel_nibble_swap":
        p1 = (b0 << 4) | ((b2 >> 4) & 0x0F)
        p0 = (b1 << 4) | (b2 & 0x0F)

    else:
        # fallback: standard
        p0 = (b0 << 4) | (b2 & 0x0F)
        p1 = (b1 << 4) | ((b2 >> 4) & 0x0F)

    # Interleave p0, p1: [p0_0, p1_0, p0_1, p1_1, ...]
    pixels = np.empty(n_triplets * 2, dtype=np.uint32)
    pixels[0::2] = p0
    pixels[1::2] = p1

    # Clamp to 12-bit range (values should already be ≤4095 but be safe)
    pixels = np.clip(pixels, 0, 4095)

    if align == "left":
        # Scale to full 16-bit range (multiply by 16 = shift left 4)
        pixels = (pixels << 4).astype(np.uint16)
    else:
        pixels = pixels.astype(np.uint16)

    return pixels


# ═══════════════════════════════════════════════════════════════════════════════
# Camera Thread
# ═══════════════════════════════════════════════════════════════════════════════

class CameraThread(QThread):
    raw_frame_ready = pyqtSignal(object, object)  # raw_bytes, metadata

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._consumer_ready = True  # drop frames while UI is still processing
        self.cam = None
        self.config = None
        self.fps = 5

    def notify_consumer_ready(self):
        self._consumer_ready = True

    def init_camera(self):
        if not HAS_CAMERA:
            return False
        self.cam = Picamera2()
        res = self.cam.sensor_resolution
        self.config = self.cam.create_preview_configuration(
            main={"size": res},
            controls={
                "FrameRate": self.fps,
                "FrameDurationLimits": (1000, 1000000 // self.fps),
                "NoiseReductionMode": 0,
            },
            raw={"size": res},
            transform=Transform(vflip=False, hflip=False),
        )
        self.cam.configure(self.config)
        # Read the actual stride picamera2 filled in after configure
        self.raw_stride = self.cam.camera_configuration()["raw"]["stride"]
        self.cam.start()
        # Fixed exposure: AE/AGC off, 40 ms, gain 1.0
        self.cam.set_controls({
            "AeEnable": False,
            "ExposureTime": 40000,
            "AnalogueGain": 1.0,
        })
        return True

    def run(self):
        self._running = True
        if not HAS_CAMERA:
            self._run_simulation()
            return

        try:
            while self._running:
                buffers, metadata = self.cam.capture_buffers(["raw"])
                if self._consumer_ready:
                    self._consumer_ready = False
                    raw_bytes = np.frombuffer(buffers[0], dtype=np.uint8).copy()
                    self.raw_frame_ready.emit(raw_bytes, metadata)
        except Exception as e:
            print(f"Camera error: {e}")

    def _run_simulation(self):
        """Generate fake 12-bit CSI2P data for testing without a camera."""
        import time
        # Fake sensor: 640x480, stride = 640*3//2 = 960 bytes/row
        width, height = 640, 480
        stride = (width * 3) // 2  # 12bit packed: 3 bytes per 2 pixels
        t = 0
        while self._running:
            t += 0.1
            # Simulate a gradient image with some noise
            row_values = np.linspace(0, 4095, width, dtype=np.uint32)
            row_values = (row_values + int(np.sin(t) * 512 + 512)) % 4096
            
            all_bytes = []
            for y in range(height):
                brightness = (y / height + np.sin(t + y * 0.05) * 0.1)
                brightness = np.clip(brightness, 0, 1)
                pix = (row_values * brightness + np.random.randint(0, 20, width)).astype(np.uint32)
                pix = np.clip(pix, 0, 4095)
                # Pack pairs into 3 bytes (standard CSI2P)
                p0 = pix[0::2]
                p1 = pix[1::2]
                n_pairs = min(len(p0), len(p1))
                row_bytes = np.zeros(n_pairs * 3, dtype=np.uint8)
                row_bytes[0::3] = (p0[:n_pairs] >> 4) & 0xFF
                row_bytes[1::3] = (p1[:n_pairs] >> 4) & 0xFF
                row_bytes[2::3] = ((p1[:n_pairs] & 0x0F) << 4) | (p0[:n_pairs] & 0x0F)
                all_bytes.append(row_bytes[:stride])
            
            if self._consumer_ready:
                self._consumer_ready = False
                raw_bytes = np.concatenate(all_bytes)
                metadata = {"ExposureTime": 10000, "AnalogueGain": 1.0, "DigitalGain": 1.0}
                self.raw_frame_ready.emit(raw_bytes, metadata)
            time.sleep(1.0 / 10)

    def stop(self):
        self._running = False
        if self.cam:
            try:
                self.cam.stop()
                self.cam.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# Histogram Widget (pyqtgraph-based, fast)
# ═══════════════════════════════════════════════════════════════════════════════

class HistogramWidget(pg.GraphicsLayoutWidget):
    EXP_MIN_US = 100
    EXP_MAX_US = 200000

    exposure_changed = pyqtSignal(int)  # µs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackground("#0d0d0d")
        self.plot = self.addPlot()
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=False, y=True, alpha=0.15)
        self.plot.hideAxis('bottom')
        self.plot.getAxis('left').setStyle(tickFont=QFont("Courier New", 7))
        self.plot.getAxis('left').setPen(pg.mkPen('#444'))
        self.plot.getAxis('left').setTextPen(pg.mkPen('#666'))
        self.plot.setXRange(0, 65535, padding=0.01)

        # Three curves: R, G, B (or luminance if grayscale)
        self.curve_r = self.plot.plot(pen=pg.mkPen(color=(220, 60, 60, 180), width=1))
        self.curve_g = self.plot.plot(pen=pg.mkPen(color=(60, 200, 80, 180), width=1))
        self.curve_b = self.plot.plot(pen=pg.mkPen(color=(60, 120, 220, 180), width=1))
        self.curve_lum = self.plot.plot(pen=pg.mkPen(color=(200, 200, 200, 220), width=1.5))

        # Clipping indicator at true 12-bit left-aligned max (4095 << 4 = 65520)
        clip_line = pg.InfiniteLine(pos=65520, angle=90, pen=pg.mkPen('#ff4444', width=1, style=Qt.DashLine))
        self.plot.addItem(clip_line)

        # Draggable exposure cursor
        init_x = self._exp_to_x(40000)
        self.exposure_line = pg.InfiniteLine(
            pos=init_x, angle=90,
            pen=pg.mkPen('#f0a500', width=2),
            movable=True,
            label='40.0 ms',
            labelOpts={'position': 0.92, 'color': '#f0a500',
                       'fill': pg.mkBrush('#0d0d0dcc'),
                       'movable': True},
        )
        self.plot.addItem(self.exposure_line)
        self.exposure_line.sigPositionChanged.connect(self._on_exposure_dragged)

        self._show_rgb = True
        self.bins = np.linspace(0, 65536, 257)  # 256 bins
        self.bin_centers = (self.bins[:-1] + self.bins[1:]) / 2

    def _exp_to_x(self, exp_us):
        """Map exposure time (µs) to histogram x position (0–65535)."""
        return (exp_us - self.EXP_MIN_US) / (self.EXP_MAX_US - self.EXP_MIN_US) * 65535

    def _x_to_exp(self, x):
        """Map histogram x position (0–65535) to exposure time (µs)."""
        return int(self.EXP_MIN_US + (max(0.0, min(65535.0, x)) / 65535) * (self.EXP_MAX_US - self.EXP_MIN_US))

    def _on_exposure_dragged(self):
        exp_us = self._x_to_exp(self.exposure_line.value())
        self.exposure_line.label.setFormat(f'{exp_us / 1000:.1f} ms')
        self.exposure_changed.emit(exp_us)

    def update_histogram(self, pixels_16bit: np.ndarray, width: int, height: int, bayer_pattern: str = "RGGB"):
        """
        pixels_16bit: flat uint16 array, row-major, Bayer mosaic
        We demosaic naively by extracting R/G/B channels from Bayer positions.
        """
        if len(pixels_16bit) < width * height:
            return

        try:
            img = pixels_16bit[:width * height].reshape(height, width)
        except ValueError:
            return

        # Bayer channel extraction with spatial subsampling:
        # 1 block every 4 horizontally, 1 block-row every 8 vertically.
        # Each channel array is already at half resolution (one element per Bayer block),
        # so ::4 cols and ::8 rows gives the requested decimation.
        if bayer_pattern in ("RGGB", "BGGR"):
            r  = img[0::2, 0::2][::8, ::4].ravel()
            g1 = img[0::2, 1::2][::8, ::4].ravel()
            g2 = img[1::2, 0::2][::8, ::4].ravel()
            b  = img[1::2, 1::2][::8, ::4].ravel()
            if bayer_pattern == "BGGR":
                r, b = b, r
        else:  # GRBG, GBRG fallback
            r  = img[0::2, 1::2][::8, ::4].ravel()
            g1 = img[0::2, 0::2][::8, ::4].ravel()
            g2 = img[1::2, 1::2][::8, ::4].ravel()
            b  = img[1::2, 0::2][::8, ::4].ravel()

        g = np.concatenate([g1, g2])

        hr, _ = np.histogram(r,  bins=self.bins)
        hg, _ = np.histogram(g,  bins=self.bins)
        hb, _ = np.histogram(b,  bins=self.bins)
        lum = (hr.astype(float) * 0.2126 + hg.astype(float) * 0.7152 + hb.astype(float) * 0.0722)

        # Log scale for visibility
        hr_log  = np.log1p(hr.astype(float))
        hg_log  = np.log1p(hg.astype(float))
        hb_log  = np.log1p(hb.astype(float))
        lum_log = np.log1p(lum)

        self.curve_r.setData(self.bin_centers, hr_log)
        self.curve_g.setData(self.bin_centers, hg_log)
        self.curve_b.setData(self.bin_centers, hb_log)
        self.curve_lum.setData(self.bin_centers, lum_log)

        # Auto-range Y
        max_val = max(hr_log.max(), hg_log.max(), hb_log.max(), 1.0)
        self.plot.setYRange(0, max_val * 1.05, padding=0)


# ═══════════════════════════════════════════════════════════════════════════════
# Preview Widget — converts raw 16-bit Bayer to displayable QPixmap
# ═══════════════════════════════════════════════════════════════════════════════

class PreviewWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #080808; border: 1px solid #1e1e1e;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)

    def display_raw(self, pixels_16bit: np.ndarray, width: int, height: int,
                    bayer_pattern: str = "RGGB", gain: float = 1.0):
        """Simple Bayer → RGB conversion for preview (2x2 block average)."""
        if len(pixels_16bit) < width * height:
            return

        try:
            img = pixels_16bit[:width * height].reshape(height, width)
        except ValueError:
            return

        # Downsample to half resolution via 2x2 Bayer block
        h2, w2 = height // 2, width // 2
        r  = img[0::2, 0::2].astype(np.float32)[:h2, :w2]
        g1 = img[0::2, 1::2].astype(np.float32)[:h2, :w2]
        g2 = img[1::2, 0::2].astype(np.float32)[:h2, :w2]
        b  = img[1::2, 1::2].astype(np.float32)[:h2, :w2]

        if bayer_pattern == "BGGR":
            r, b = b, r
        elif bayer_pattern == "GRBG":
            r, g1, b = g1, r, b
        elif bayer_pattern == "GBRG":
            r, g1, b = g2, g1, r

        g = (g1 + g2) * 0.5

        # Normalize to 8-bit with gain
        scale = gain / 65535.0 * 255.0
        r8 = np.clip(r * scale, 0, 255).astype(np.uint8)
        g8 = np.clip(g * scale, 0, 255).astype(np.uint8)
        b8 = np.clip(b * scale, 0, 255).astype(np.uint8)

        rgb = np.stack([r8, g8, b8], axis=2)
        rgb_c = np.ascontiguousarray(rgb)

        qimg = QImage(rgb_c.data, w2, h2, w2 * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Scale to widget while keeping aspect
        w_size = self.width()
        h_size = self.height()
        pixmap = pixmap.scaled(w_size, h_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)


# ═══════════════════════════════════════════════════════════════════════════════
# Info Bar
# ═══════════════════════════════════════════════════════════════════════════════

class InfoBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(20)

        style = "color: #888; font-family: 'Courier New', monospace; font-size: 11px;"
        self.lbl_exp   = QLabel("EXP: —", self)
        self.lbl_gain  = QLabel("GAIN: —", self)
        self.lbl_fps   = QLabel("FPS: —", self)
        self.lbl_mode  = QLabel("MODE: —", self)
        self.lbl_sim   = QLabel("⚠ SIMULATION" if not HAS_CAMERA else "", self)

        for lbl in [self.lbl_exp, self.lbl_gain, self.lbl_fps, self.lbl_mode, self.lbl_sim]:
            lbl.setStyleSheet(style)
            layout.addWidget(lbl)

        if not HAS_CAMERA:
            self.lbl_sim.setStyleSheet("color: #f0a500; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")

        layout.addStretch()
        self._last_time = None
        self._fps_acc = []

    def update_meta(self, metadata: dict, unpack_mode_name: str):
        import time
        now = time.time()
        if self._last_time:
            self._fps_acc.append(1.0 / max(now - self._last_time, 0.001))
            if len(self._fps_acc) > 10:
                self._fps_acc.pop(0)
        self._last_time = now

        exp = metadata.get("ExposureTime", 0)
        gain = metadata.get("AnalogueGain", 0.0)
        fps = np.mean(self._fps_acc) if self._fps_acc else 0

        self.lbl_exp.setText(f"EXP: {exp/1000:.1f}ms")
        self.lbl_gain.setText(f"GAIN: {gain:.2f}x")
        self.lbl_fps.setText(f"FPS: {fps:.1f}")
        self.lbl_mode.setText(f"UNPACK: {unpack_mode_name[:20]}")


# ═══════════════════════════════════════════════════════════════════════════════
# Controls Panel
# ═══════════════════════════════════════════════════════════════════════════════

class ControlsPanel(QWidget):
    unpack_changed = pyqtSignal(str)
    align_changed  = pyqtSignal(str)
    gain_changed   = pyqtSignal(float)
    bayer_changed  = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QWidget { background: #0d0d0d; color: #c8c8c8; }
            QGroupBox {
                border: 1px solid #222;
                border-radius: 3px;
                margin-top: 8px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #555;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QComboBox {
                background: #141414;
                border: 1px solid #2a2a2a;
                border-radius: 2px;
                padding: 4px 6px;
                color: #d0d0d0;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                selection-background-color: #1a3a5a;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #555; margin-right: 5px; }
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #888;
            }
            QSlider::groove:horizontal {
                background: #1a1a1a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3a7abf;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #1e4e7a;
                border-radius: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Title ───────────────────────────────────────────────
        title = QLabel("RAW INSPECTOR")
        title.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: bold;
            color: #3a7abf;
            letter-spacing: 4px;
            padding: 4px 0 8px 0;
            border-bottom: 1px solid #1a1a1a;
        """)
        layout.addWidget(title)

        sub = QLabel("12-BIT CSI2P UNPACKER")
        sub.setStyleSheet("font-size: 9px; color: #3a3a3a; letter-spacing: 3px; font-family: 'Courier New';")
        layout.addWidget(sub)

        # ── Unpack Mode ─────────────────────────────────────────
        grp_unpack = QGroupBox("UNPACK MODE")
        grp_layout = QVBoxLayout(grp_unpack)
        grp_layout.setSpacing(4)

        self.mode_combo = QComboBox()
        mode_names_short = [
            "Standard CSI2P  (P0=B0+B2lo, P1=B1+B2hi)",
            "Nibble swap      (P0=B0+B2hi, P1=B1+B2lo)",
            "Byte swap        (P0=B1+B2lo, P1=B0+B2hi)",
            "Byte+nibble swap (P0=B1+B2hi, P1=B0+B2lo)",
            "LSB-first        (P0=B2lo<<8|B0)",
            "Big-endian 16b   (byte-swap each word)",
            "Pixel swap       (standard + P0↔P1)",
            "Pixel+nibble     (swapped + nibbles)",
        ]
        self.mode_keys = list(UNPACK_MODES.values())
        for name in mode_names_short:
            self.mode_combo.addItem(name)

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        grp_layout.addWidget(self.mode_combo)

        # Mode description
        self.mode_desc = QLabel()
        self.mode_desc.setWordWrap(True)
        self.mode_desc.setStyleSheet("color: #456; font-size: 9px; font-family: 'Courier New'; padding: 4px;")
        self._update_mode_desc(0)
        grp_layout.addWidget(self.mode_desc)

        layout.addWidget(grp_unpack)

        # ── Alignment ───────────────────────────────────────────
        grp_align = QGroupBox("BIT ALIGNMENT")
        align_layout = QVBoxLayout(grp_align)

        self.align_combo = QComboBox()
        self.align_combo.addItem("Left-aligned  (×16 → full 16-bit range)")
        self.align_combo.addItem("Right-aligned (12-bit in 16-bit container)")
        self.align_combo.currentIndexChanged.connect(self._on_align_changed)
        align_layout.addWidget(self.align_combo)

        align_note = QLabel("Left: maps 0..4095 → 0..65520\nRight: raw value 0..4095")
        align_note.setStyleSheet("color: #3a3a3a; font-size: 9px; font-family: 'Courier New'; padding: 2px 4px;")
        align_layout.addWidget(align_note)
        layout.addWidget(grp_align)

        # ── Bayer Pattern ───────────────────────────────────────
        grp_bayer = QGroupBox("BAYER PATTERN")
        bayer_layout = QVBoxLayout(grp_bayer)
        self.bayer_combo = QComboBox()
        for pat in ["RGGB", "BGGR", "GRBG", "GBRG"]:
            self.bayer_combo.addItem(pat)
        self.bayer_combo.setCurrentText("BGGR")
        self.bayer_combo.currentTextChanged.connect(self.bayer_changed)
        bayer_layout.addWidget(self.bayer_combo)

        bayer_note = QLabel("IMX477 (RPi HQ Cam) = BGGR")
        bayer_note.setStyleSheet("color: #3a3a3a; font-size: 9px; font-family: 'Courier New'; padding: 2px 4px;")
        bayer_layout.addWidget(bayer_note)
        layout.addWidget(grp_bayer)

        # ── Preview Gain ────────────────────────────────────────
        grp_gain = QGroupBox("PREVIEW GAIN")
        gain_layout = QVBoxLayout(grp_gain)

        self.gain_label = QLabel("1.0×")
        self.gain_label.setStyleSheet("color: #3a7abf; font-size: 12px; font-family: 'Courier New'; font-weight: bold;")
        gain_layout.addWidget(self.gain_label)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(1, 64)
        self.gain_slider.setValue(4)  # 1.0x
        self.gain_slider.valueChanged.connect(self._on_gain_changed)
        gain_layout.addWidget(self.gain_slider)

        gain_range = QLabel("0.25×  ─────────────  16×")
        gain_range.setStyleSheet("color: #333; font-size: 9px; font-family: 'Courier New';")
        gain_layout.addWidget(gain_range)
        layout.addWidget(grp_gain)

        # ── Sensor info ─────────────────────────────────────────
        grp_info = QGroupBox("SENSOR INFO")
        info_layout = QVBoxLayout(grp_info)
        self.lbl_res = QLabel("Resolution: detecting…")
        self.lbl_stride = QLabel("Stride: —")
        self.lbl_format = QLabel("Format: SBGGR12_CSI2P")
        for lbl in [self.lbl_res, self.lbl_stride, self.lbl_format]:
            info_layout.addWidget(lbl)
        layout.addWidget(grp_info)

        layout.addStretch()

        # ── Bit diagram ─────────────────────────────────────────
        grp_diag = QGroupBox("3-BYTE ENCODING DIAGRAM")
        diag_layout = QVBoxLayout(grp_diag)
        self.diag_label = QLabel()
        self.diag_label.setWordWrap(True)
        self.diag_label.setStyleSheet("color: #2a5a8a; font-size: 9px; font-family: 'Courier New'; padding: 2px;")
        self._update_diagram(0)
        diag_layout.addWidget(self.diag_label)
        layout.addWidget(grp_diag)

    def _on_mode_changed(self, idx):
        key = self.mode_keys[idx]
        self.unpack_changed.emit(key)
        self._update_mode_desc(idx)
        self._update_diagram(idx)

    def _on_align_changed(self, idx):
        self.align_changed.emit("left" if idx == 0 else "right")

    def _on_gain_changed(self, val):
        gain = val / 4.0
        self.gain_label.setText(f"{gain:.2f}×")
        self.gain_changed.emit(gain)

    def _update_mode_desc(self, idx):
        descs = [
            "MIPI CSI-2 standard. Upper 8 bits of each pixel in B0/B1, low nibbles packed in B2 (P0 in bits 3:0, P1 in bits 7:4).",
            "Same as standard but the nibbles in B2 are swapped: P0 gets B2[7:4], P1 gets B2[3:0].",
            "B0 and B1 roles are exchanged. P0 uses B1 as MSByte, P1 uses B0.",
            "Both byte order and nibble order are inverted relative to standard.",
            "LSB-first interpretation: low 4 bits from B2, upper 8 bits from B0/B1 inverted.",
            "Standard unpack then each resulting 16-bit word has its bytes swapped (big-endian).",
            "Standard unpack but the two resulting pixels in each triplet are exchanged.",
            "Pixel pair swapped AND nibbles swapped.",
        ]
        self.mode_desc.setText(descs[idx] if idx < len(descs) else "")

    def _update_diagram(self, idx):
        diagrams = [
            "B0: A11 A10 A9  A8  A7  A6  A5  A4\nB1: B11 B10 B9  B8  B7  B6  B5  B4\nB2: B3  B2  B1  B0  A3  A2  A1  A0",
            "B0: A11 A10 A9  A8  A7  A6  A5  A4\nB1: B11 B10 B9  B8  B7  B6  B5  B4\nB2: A3  A2  A1  A0  B3  B2  B1  B0",
            "B0: B11 B10 B9  B8  B7  B6  B5  B4\nB1: A11 A10 A9  A8  A7  A6  A5  A4\nB2: B3  B2  B1  B0  A3  A2  A1  A0",
            "B0: B11 B10 B9  B8  B7  B6  B5  B4\nB1: A11 A10 A9  A8  A7  A6  A5  A4\nB2: A3  A2  A1  A0  B3  B2  B1  B0",
            "B0: A7  A6  A5  A4  A3  A2  A1  A0\nB1: B7  B6  B5  B4  B3  B2  B1  B0\nB2: B11 B10 B9  B8  A11 A10 A9  A8",
            "B0: A3  A2  A1  A0 [lo-byte of A]\nB1: B3  B2  B1  B0 [lo-byte of B]\nB2: B11..B4 then A11..A4 → swapped",
            "B0: B11 B10 B9  B8  B7  B6  B5  B4  ← pixel B\nB1: A11 A10 A9  A8  A7  A6  A5  A4  ← pixel A\nB2: A3  A2  A1  A0  B3  B2  B1  B0",
            "B0: B11..B4  B1: A11..A4\nB2: B3..B0 A3..A0\n(pixel pair swapped + nibbles swapped)",
        ]
        self.diag_label.setText(diagrams[idx] if idx < len(diagrams) else "")

    def set_sensor_info(self, width, height, stride):
        self.lbl_res.setText(f"Resolution: {width}×{height}")
        self.lbl_stride.setText(f"Stride: {stride} bytes/row")


# ═══════════════════════════════════════════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════════════════════════════════════════

STYLESHEET = """
QMainWindow, QWidget#central {
    background: #080808;
}
QSplitter::handle {
    background: #1a1a1a;
    width: 2px;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAW Inspector — 12-bit CSI2P Unpacker")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(STYLESHEET)

        # State
        self.unpack_mode = "standard"
        self.align_mode  = "left"
        self.preview_gain = 1.0
        self.bayer_pattern = "BGGR"
        self.sensor_width  = 640
        self.sensor_height = 480
        self.sensor_stride = 960  # default for 640px 12bit packed

        # Camera thread
        self.cam_thread = CameraThread()
        self.cam_thread.raw_frame_ready.connect(self._on_raw_frame)

        # Build UI
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left: controls
        self.controls = ControlsPanel()
        self.controls.unpack_changed.connect(self._on_unpack_changed)
        self.controls.align_changed.connect(self._on_align_changed)
        self.controls.gain_changed.connect(self._on_gain_changed)
        self.controls.bayer_changed.connect(self._on_bayer_changed)
        root.addWidget(self.controls)


        # Right: preview + histogram stacked vertically
        right_widget = QWidget()
        right_widget.setStyleSheet("background: #090909;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Info bar
        self.info_bar = InfoBar()
        self.info_bar.setStyleSheet("background: #0a0a0a; border-bottom: 1px solid #1a1a1a;")
        right_layout.addWidget(self.info_bar)

        # Preview (top half) + histogram (bottom half)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(4)

        # Preview area
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.NoFrame)
        preview_v = QVBoxLayout(preview_frame)
        preview_v.setContentsMargins(0, 0, 0, 0)
        preview_label = QLabel("LIVE PREVIEW")
        preview_label.setStyleSheet("""
            color: #2a2a2a; font-family: 'Courier New'; font-size: 9px;
            letter-spacing: 3px; padding: 2px 4px;
            background: #0a0a0a; border-bottom: 1px solid #141414;
        """)
        preview_v.addWidget(preview_label)
        self.preview = PreviewWidget()
        preview_v.addWidget(self.preview)
        content_layout.addWidget(preview_frame, stretch=3)

        # Histogram area
        hist_frame = QFrame()
        hist_frame.setFrameShape(QFrame.NoFrame)
        hist_v = QVBoxLayout(hist_frame)
        hist_v.setContentsMargins(0, 0, 0, 0)
        hist_label = QLabel("HISTOGRAM  (R · G · B · LUM)")
        hist_label.setStyleSheet("""
            color: #2a2a2a; font-family: 'Courier New'; font-size: 9px;
            letter-spacing: 3px; padding: 2px 4px;
            background: #0a0a0a; border-bottom: 1px solid #141414;
        """)
        hist_v.addWidget(hist_label)
        self.histogram = HistogramWidget()
        self.histogram.exposure_changed.connect(self._on_exposure_changed)
        hist_v.addWidget(self.histogram)
        content_layout.addWidget(hist_frame, stretch=2)

        right_layout.addWidget(content)
        root.addWidget(right_widget, stretch=1)

        # Start camera
        self._start_camera()

    def _start_camera(self):
        if HAS_CAMERA:
            ok = self.cam_thread.init_camera()
            if ok and self.cam_thread.config:
                raw_cfg = self.cam_thread.config.get("raw", {})
                size = raw_cfg.get("size", (640, 480))
                self.sensor_width, self.sensor_height = size
                self.sensor_stride = self.cam_thread.raw_stride  # actual stride from picamera2
                self.controls.set_sensor_info(self.sensor_width, self.sensor_height, self.sensor_stride)
        else:
            # Simulation: use fake 640×480
            self.sensor_width, self.sensor_height = 640, 480
            self.sensor_stride = 960
            self.controls.set_sensor_info(self.sensor_width, self.sensor_height, self.sensor_stride)

        self.cam_thread.start()

    def _on_raw_frame(self, raw_bytes: np.ndarray, metadata: dict):
        # Strip row padding: each row is sensor_stride bytes but only
        # width*3//2 bytes contain pixel data; excess is libcamera alignment padding.
        row_bytes = (self.sensor_width * 3) // 2
        if self.sensor_stride != row_bytes:
            raw_2d = raw_bytes.reshape(self.sensor_height, self.sensor_stride)
            raw_bytes = np.ascontiguousarray(raw_2d[:, :row_bytes]).ravel()

        # Unpack
        pixels = unpack_12bit(raw_bytes, self.unpack_mode, self.align_mode)

        # Update preview (disabled for histogram performance testing)
        # self.preview.display_raw(
        #     pixels, self.sensor_width, self.sensor_height,
        #     self.bayer_pattern, self.preview_gain
        # )

        # Update histogram
        self.histogram.update_histogram(
            pixels, self.sensor_width, self.sensor_height,
            self.bayer_pattern
        )

        # Update info bar
        mode_idx = self.controls.mode_combo.currentIndex()
        mode_name = self.controls.mode_combo.itemText(mode_idx)[:25]
        self.info_bar.update_meta(metadata, mode_name)

        # Allow the camera thread to emit the next frame
        self.cam_thread.notify_consumer_ready()

    def _on_unpack_changed(self, mode: str):
        self.unpack_mode = mode

    def _on_align_changed(self, align: str):
        self.align_mode = align

    def _on_gain_changed(self, gain: float):
        self.preview_gain = gain

    def _on_bayer_changed(self, pattern: str):
        self.bayer_pattern = pattern

    def _on_exposure_changed(self, exp_us: int):
        if HAS_CAMERA and self.cam_thread.cam:
            self.cam_thread.cam.set_controls({"ExposureTime": exp_us})

    def closeEvent(self, event):
        self.cam_thread.stop()
        self.cam_thread.wait(2000)
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # PyQtGraph config
    pg.setConfigOptions(antialias=False, useOpenGL=False)
    pg.setConfigOption('background', '#0d0d0d')
    pg.setConfigOption('foreground', '#555555')

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(8, 8, 8))
    palette.setColor(QPalette.WindowText,      QColor(200, 200, 200))
    palette.setColor(QPalette.Base,            QColor(13, 13, 13))
    palette.setColor(QPalette.AlternateBase,   QColor(18, 18, 18))
    palette.setColor(QPalette.Text,            QColor(200, 200, 200))
    palette.setColor(QPalette.Button,          QColor(20, 20, 20))
    palette.setColor(QPalette.ButtonText,      QColor(200, 200, 200))
    palette.setColor(QPalette.Highlight,       QColor(30, 80, 130))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
