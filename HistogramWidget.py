import sys
import math

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import Qt, QSize

from cffi import FFI

ffi=FFI()
ffi.cdef("""
  void draw_histogram(uint8_t *buffer, int width, int height, int x, int y);
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
        x=event.pos().x()
        y=event.pos().y()
        print(f"x={x}, y={y}")
        if event.button() == Qt.LeftButton: # Handle left mouse clicks
            self.drawHistogram(event.pos().x(), event.pos().y())

    def drawHistogram(self, x, y):
        self.image.fill(0)
        lib.draw_histogram(ffi.cast("uint8_t *",self.image.bits()), self.image.width(), self.image.height(),x, y)
        self.update()




