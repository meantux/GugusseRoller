import sys
import math

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, QSize

from cffi import FFI

ffi=FFI()
ffi.cdef("""
  void draw_histogram(unsigned char *buffer, int width, int height);
""")
lib = ffi.dlopen("./histogram_lib.so")

class HistogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage()
        self.setMinimumSize(200, 200)

    def sizeHint(self):
        return QSize(200, 200)

    def minimumSizeHint(self):
        return QSize(200, 200)

    def resizeEvent(self, event):
        new_size = event.size()
        print(f"New size: {new_size.width()}x{new_size.height()}")
        self.image = QImage(new_size, QImage.Format_RGB32)
        self.image.fill(0)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

    def setData(self, data):
        self.data = data
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: # Handle left mouse clicks
            self.drawHistogram()

    def drawHistogram(self):
        lib.draw_histogram(ffi.cast("unsigned char *",self.image.bits()), self.image.width(), self.image.height())
        self.update()




