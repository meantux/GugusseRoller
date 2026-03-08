# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GugusseRoller is a DIY film scanner controller running on a **Raspberry Pi** (latest Raspbian). It drives 3 stepper motors, controls a Raspberry Pi HQ Camera (IMX477), reads GPIO sensors, and transfers captured frames via FTP or local copy.

**This software cannot run on any workstation.** It requires Raspberry Pi hardware: GPIO pins for motor control and sensors, the RPi HQ Camera via libcamera/picamera2, and RPi.GPIO. Do not attempt to run, test, or simulate any of it off the Pi. No cross-platform workarounds.

## C++ Conversion in Progress

The codebase is being converted from Python to C++. See **STEPS.TXT** for the full plan and rationale. Work started on Step 1 (camera + DNG writer). C++ files live in `cpp/`.

### C++ stack chosen
| Replaces | C++ library |
|---|---|
| PyQt5 | Qt6 C++ |
| picamera2 | libcamera C++ API |
| RPi.GPIO | libgpiod / gpiodcxx |
| ConfigFiles (json) | QJsonDocument |
| ftplib | libcurl |

### cpp/ — Step 1 files (camera + DNG)
- `cpp/GCamera.h` / `cpp/GCamera.cpp` — synchronous libcamera wrapper. Reads CFA pattern from `properties::draft::ColorFilterArrangement` post-configure (accounts for flip transforms). Uses a `deque` + mutex + condition_variable for thread-safe handoff. Requests are reused and requeued immediately to keep the pipeline primed.
- `cpp/DngWriter.h` / `cpp/DngWriter.cpp` — libtiff-based DNG writer. Converts CSI2P packing to TIFF-standard 12-bit packing row-by-row. Custom DNG tags registered via `TIFFSetTagExtender`. Atomic write via `.tmp` + rename.
- `cpp/main_test.cpp` — standalone test: init camera, capture one frame, write DNG, report timing.
- `cpp/CMakeLists.txt` — build file.

### Building the C++ code (on the Pi)
```bash
cd cpp
cmake -B build
cmake --build build
./build/camera_test /tmp/test.dng
exiftool /tmp/test.dng
```

### Key design decisions (do not revisit without good reason)
- **12-bit packed storage** in DNG — CSI2P (libcamera format) and TIFF-standard 12-bit are different packings; `convertRowCsi2pToTiff12()` converts on the fly per row, no extra full buffer needed.
- **Single strip** DNG — entire image in one `TIFFWriteRawStrip` call, simpler IFD.
- **ColorMatrix1** — uses per-frame `controls::ColourCorrectionMatrix` from libcamera metadata if available, falls back to hardcoded IMX477 D65 reference matrix.
- **Future 3-exposure bracketing** — channel splicing happens in CSI2P format on the raw buffer before DNG write, using a 2-buffer strategy (canvas + one temp). See STEPS.TXT for the sequence.
- **"learn pin" to Arduino is deprecated** — removed from Step 2 motor design.

## Running the Python Applications

```bash
# Main GUI application
python3 GugusseGUI.py

# Setup wizard for motor direction and FTP/local export config
python3 MotorsAndFtpSetup.py

# Standalone RAW viewer / 12-bit CSI2P histogram inspector
python3 raw_viewer.py

# Control lights from command line
python3 Lights.py <on|off|red|green|blue|cyan|magenta|yellow>
```

No build step for Python — all files run directly.

## Python Architecture

### Signal/Thread Model

The GUI runs on the Qt main thread. Background work uses `QThread` with `pyqtSignal` for cross-thread communication. The pattern throughout is:
- A `QThread` subclass does blocking hardware I/O
- It emits a `signal` (always typed `"PyQt_PyObject"`) with string messages
- The connected slot on the main thread parses the message and updates the UI

String messages from `CaptureLoop`/`FtpThread` follow ad-hoc protocols:
- `"xfer,<filename>"` → update last-transferred file label
- `"syncMotors"` → refresh motor power-state icons
- `"turning lights off"` → turn off lights
- `"spdchg,<motorname>,<speed>"` → update speedmeter label
- `"Capture stopped!"` → re-enable UI widgets

### Capture Pipeline

1. `CaptureLoop` (QThread) → calls `FrameSequence.frameAdvance()` in a loop
2. `FrameSequence.frameAdvance()` → calls `GCamera.captureCycle()` which writes a file to `/dev/shm/<num>.ext`, then renames it to `/dev/shm/complete/<num>.ext`
3. `FtpThread` or `LocalThread` (Python Thread) → polls `/dev/shm/complete/` every second and transfers/moves files out

The `/dev/shm/complete/` directory acts as a FIFO queue between capture and export. If more than 6 files accumulate, capture pauses for up to 5 minutes.

### Motor Control

`TrinamicSilentMotor` drives Trinamic stepper drivers via 3 GPIO pins each (step, direction, enable). Two motor types have different `move()` implementations:
- **filmdrive** (`isFilmDrive: true`) — counts steps to the hole-detection sensor
- **feeder / pickup** (`isFilmDrive: false`) — times the move to an arm-position sensor

Speed is auto-adjusted each cycle via `calculateNewSpeed()` using a rolling 6-sample history compared to `targetTime`.

### Configuration Files

All config is stored as JSON in the working directory and managed by `ConfigFiles` (subclass of `dict`):
- `GugusseSettings.json` — camera settings (exposure, ISO, white balance, fps, flip)
- `hardwarecfg.json` — GPIO pin assignments, film format parameters per motor, lights pins, save mode
- `ftp.json` — FTP server credentials and path
- `captureModes.json` — capture mode definitions (DNG, singleJpg, bracketing)

`ConfigFiles` auto-creates files with defaults on first run. Saves atomically via a temp file + `shutil.move`.

### UI Layout (GugusseGUI.py)

`MainWindow` assembles all widget modules:
- Row 1: Exposure mode, exposure slider, ISO
- Row 2: White balance mode, freeze WB, red/blue gain
- Row 3: Brightness, contrast, sharpness, saturation
- Bottom left: flip checkboxes, save settings; 3 motor widgets (feeder/filmdrive/pickup with CW/CCW manual buttons); lights selector, project name, film format, capture mode, reels direction, snapshot/run-stop buttons, sensor monitoring
- Bottom right: live camera preview (`QGlPicamera2`), click to zoom/unzoom

### Widget Pattern

Most UI controls follow a consistent pattern:
- Subclass a Qt widget (QSlider, QComboBox, QPushButton, etc.)
- Store a companion `QLabel` returned by `getLabel()`, inserted separately into layouts
- Implement `syncCamera()` to push current state to `picam2.set_controls()`
- Read/write from `win.settings` (the `ConfigFiles` dict) for persistence

### raw_viewer.py

Standalone diagnostic tool for exploring 12-bit CSI2P raw data from the IMX477. Key behaviours:
- `CameraThread` emits frames only when the UI signals it is ready (`_consumer_ready` flag) — prevents Qt event queue overflow with 18.5 MB frames.
- Row padding is stripped before unpacking: libcamera stride (6112 bytes) ≠ pixel data width (6084 bytes for 4056px); `_on_raw_frame` reshapes to `(height, stride)` and slices `[:, :row_bytes]`.
- Histogram subsamples 1 BGGR block per 4 horizontally, 1 row per 8 vertically for performance.
- Draggable orange `InfiniteLine` on histogram controls camera `ExposureTime` live (100 µs – 200 ms range).
- IMX477 black level pedestal is ~256 (12-bit), so the dark-frame peak sits at 4096 in 16-bit left-aligned space — this is normal, not a bug.
- Default Bayer pattern is BGGR (confirmed from `SBGGR12_CSI2P` format string).
- Preview rendering is currently commented out (`_on_raw_frame`) for histogram performance testing.
