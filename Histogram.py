import os
import subprocess
import numpy as np
from ctypes import CDLL, c_uint8, c_uint32, c_size_t, POINTER
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt

class HistogramCalculator:
    def __init__(self):
        base = os.path.dirname(__file__)
        self.lib_path = os.path.join(base, 'histogram.so')
        if not os.path.exists(self.lib_path):
            src = os.path.join(base, 'histogram.c')
            subprocess.check_call(['gcc', '-O3', '-shared', '-fPIC', '-o', self.lib_path, src])
        self.lib = CDLL(self.lib_path)
        self.lib.histogram_rgb8.argtypes = [POINTER(c_uint8), c_size_t,
                                            POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32)]
        self.lib.histogram_gray12.argtypes = [POINTER(c_uint8), c_size_t,
                                              POINTER(c_uint32)]

    def hist_rgb8(self, arr):
        h, w, _ = arr.shape
        pixel_count = h * w
        hist_r = np.zeros(256, dtype=np.uint32)
        hist_g = np.zeros(256, dtype=np.uint32)
        hist_b = np.zeros(256, dtype=np.uint32)
        self.lib.histogram_rgb8(arr.ctypes.data_as(POINTER(c_uint8)), pixel_count,
                                hist_r.ctypes.data_as(POINTER(c_uint32)),
                                hist_g.ctypes.data_as(POINTER(c_uint32)),
                                hist_b.ctypes.data_as(POINTER(c_uint32)))
        return hist_r, hist_g, hist_b

    def hist_gray12(self, data):
        byte_count = data.size
        hist = np.zeros(4096, dtype=np.uint32)
        self.lib.histogram_gray12(data.ctypes.data_as(POINTER(c_uint8)), byte_count,
                                  hist.ctypes.data_as(POINTER(c_uint32)))
        return hist

class HistogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None
        self.hist = None
        self.setMinimumHeight(100)

    def setHistogram(self, hist, mode):
        self.mode = mode
        if mode == 'gray12':
            self.hist = hist.reshape(256, 16).sum(axis=1)
        else:
            self.hist = hist
        self.update()

    def paintEvent(self, event):
        if self.hist is None:
            return
        painter = QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, Qt.black)
        width = rect.width()
        height = rect.height()
        if self.mode == 'rgb':
            maxv = max(h.max() for h in self.hist)
            if maxv == 0:
                return
            step = width / 256.0
            colors = [Qt.red, Qt.green, Qt.blue]
            for chan, color in zip(self.hist, colors):
                pen = QPen(color)
                painter.setPen(pen)
                for i in range(256):
                    v = chan[i] / maxv
                    painter.drawLine(int(i * step), height, int(i * step), height - int(v * height))
        else:
            maxv = self.hist.max()
            if maxv == 0:
                return
            bins = len(self.hist)
            step = width / float(bins)
            pen = QPen(Qt.white)
            painter.setPen(pen)
            for i in range(bins):
                v = self.hist[i] / maxv
                painter.drawLine(int(i * step), height, int(i * step), height - int(v * height))
