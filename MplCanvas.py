from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy
import numpy as np

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        # Optional: Customize the widget appearance
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def plot_raw_histogram(self, raw_buffer):
        raw_data = np.frombuffer(raw_buffer, dtype=np.uint8)

        # Validate the size of the buffer
        expected_size = (4056 * 3040 * 12) // 8
        assert raw_data.size == expected_size, f"Expected buffer size {expected_size}, but got {raw_data.size}"
        
        # Reshape the data to allow extraction of 12-bit values
        raw_data = raw_data.reshape(-1, 3)

        # Extract the 12-bit pixel values
        num_pixels = 4056 * 3040
        pixel_values = np.zeros(num_pixels, dtype=np.uint16)
        
        # Extract two 12-bit values from each 3-byte chunk
        pixel_values[0::2] = (raw_data[:, 0].astype(np.uint16) << 4) | (raw_data[:, 1] >> 4)
        pixel_values[1::2] = ((raw_data[:, 1] & 0x0F).astype(np.uint16) << 8) | raw_data[:, 2]
        #pixel_values[0::2] = (raw_data[:, 0].astype(np.uint16) << 4) | (raw_data[:, 1] >> 4)
        #pixel_values[1::2] = ((raw_data[:, 1] & 0x0F).astype(np.uint16) << 8) | raw_data[:, 2]
        
        # Print the max, min, and average value of the pixel values
        max_value = np.max(pixel_values)
        min_value = np.min(pixel_values)
        avg_value = np.mean(pixel_values)

        print(f"Max pixel value: {max_value}")
        print(f"Min pixel value: {min_value}")
        print(f"Average pixel value: {avg_value}")

        
        # Normalize pixel values to the range 0 to 1
        normalized_pixel_values = pixel_values / 4095.0

        # Example width of the Qt5 widget
        widget_width = 1024  # Replace with the actual width of your widget

        # Scale the normalized pixel values to the display width
        scaled_pixel_values = (normalized_pixel_values * (widget_width - 1)).astype(int)

        # Compute the histogram
        hist, bins = np.histogram(scaled_pixel_values, bins=widget_width, range=(0, widget_width - 1))

        # Plot the histogram
        self.axes.clear()
        self.axes.bar(bins[:-1], hist, width=1)
        self.axes.set_xlabel('Pixel Value')
        self.axes.set_ylabel('Frequency')
        self.axes.set_title('Histogram of Pixel Values')
        self.draw()

        
