import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QComboBox, QPushButton, QLineEdit, QTextEdit, QSplitter, QSizePolicy
from PyQt5.QtCore import Qt

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2

import CameraSettings as cs



class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("QtGugusse")
        
        with open("CameraSettings.json","rt") as h:
            self.settings=json.load(h)
        fps=self.settings["fps"]
        
        self.picam2=Picamera2()

        self.preview_config=self.picam2.create_preview_configuration({"size":(4056,3040)},controls={"FrameRate":fps,"FrameDurationLimits": (1000, 1000000//fps),"NoiseReductionMode":0})
        self.still_config=self.picam2.create_still_configuration(controls={"FrameRate":fps,"FrameDurationLimits": (1000, 1000000//fps),"NoiseReductionMode":0})
        
        print(self.preview_config)
        print(self.still_config)
        self.picam2.configure(self.preview_config)
        self.camWidget=cs.previewWindowWidget(self)
        
        self.main_layout = QVBoxLayout()
        self.out = QTextEdit()

        #topWidget=QWidget()
        #top=QHBoxLayout(topWidget)
        #topWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #self.main_layout.addLayout(top)

        
        row_layout=QHBoxLayout()
        
        # Row 1  | Exposure stuff
        self.AutoExposure=cs.AutoExposureWidget(self)
        row_layout.addWidget(self.AutoExposure.getLabel())
        row_layout.addWidget(self.AutoExposure)
        self.ExposureDual=cs.ExposureDualWidget(self)
        row_layout.addWidget(self.ExposureDual.getLabel())
        row_layout.addWidget(self.ExposureDual)
        self.Iso=cs.IsoWidget(self)
        row_layout.addWidget(self.Iso.getLabel())
        row_layout.addWidget(self.Iso)
        self.main_layout.addLayout(row_layout)
        
        row_layout=QHBoxLayout()

        # Row 2 White balance stuff
        self.WBMode=cs.WhiteBalanceModeWidget(self)
        row_layout.addWidget(self.WBMode.getLabel())
        row_layout.addWidget(self.WBMode)
        self.Freeze=cs.FreezeWidget(self)
        row_layout.addWidget(self.Freeze)
        self.RedGain=cs.ColorGainWidget(self, 0)
        row_layout.addWidget(self.RedGain.getLabel())
        row_layout.addWidget(self.RedGain)
        self.BlueGain=cs.ColorGainWidget(self, 1)
        row_layout.addWidget(self.BlueGain.getLabel())
        row_layout.addWidget(self.BlueGain)
        self.main_layout.addLayout(row_layout)
    
        
        # Row 3  | LightControl    AWB mode              WBGain1   WBGain2
        # Row 2  | Effects         Contrast              Sharpness Saturation

        

#        # Top section split into 4 rows
#        self.controls = ['Sharpness', 'Saturation', 'WBGain1', 'WBGain2', 'Exposure', 'Contrast', 'AutoCompensate', 'iso', 'Brightness']
#        controls_split = [self.controls[i:i + 4] for i in range(0, len(self.controls), 4)]
#        for controls_row in controls_split:
#            row_layout = QHBoxLayout()
#            for control in controls_row:
#                label = QLabel(control)
#                slider = QSlider(Qt.Horizontal)
#                slider.setRange(0, 100)
#                slider.valueChanged.connect(lambda value, c=control: self.on_slider_value_changed(c, value))
#                row_layout.addWidget(label)
#                row_layout.addWidget(slider)
#            self.main_layout.addLayout(row_layout)

        self.light_selector = QComboBox()
        self.light_selector.addItems(['white', 'off', 'red', 'green', 'blue', 'cyan', 'magenta','yellow'])
        self.light_selector.currentTextChanged.connect(self.on_light_selector_changed)
        self.main_layout.addWidget(self.light_selector)

        # Bottom section divided into left and right
        self.bottom_layout = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Project name field
        project_label = QLabel("Project name")
        self.project_name = QLineEdit()
        project_layout = QHBoxLayout()
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_name)
        left_layout.addLayout(project_layout)


        self.selectors_controls = ['FilmFormat', 'CaptureMode', 'ExposureMode', 'AWB', 'ReelsDirection']
        for control in self.selectors_controls:
            label = QLabel(control)
            selector = QComboBox()
            selector.addItems(['Option1', 'Option2', 'Option3'])
            selector.currentTextChanged.connect(lambda text, c=control: self.on_selector_changed(c, text))
            selector_layout = QHBoxLayout()
            selector_layout.addWidget(label)
            selector_layout.addWidget(selector)
            left_layout.addLayout(selector_layout)

        self.buttons_controls = ['hflip', 'vflip', 'SaveSettings', 'PreviewToggle', 'Run', 'Photo']
        for control in self.buttons_controls:
            button = QPushButton(control)
            button.clicked.connect(lambda _, c=control: self.on_button_clicked(c))
            left_layout.addWidget(button)

        left_widget.setLayout(left_layout)
        self.bottom_layout.addWidget(left_widget)

        # Text output area
        self.out.setReadOnly(True)
        left_layout.addWidget(self.out)
        self.main_layout.addWidget(self.bottom_layout)

        # Camera preview area
        self.bottom_layout.addWidget(self.camWidget)

        
        widget = QWidget()
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)

        # forcing a sync with the auto-exposure value will fix all exposure related values
        self.AutoExposure.syncCamera()
        self.WBMode.syncCamera()
        self.picam2.start()
        

    def getBottomLayout(self):
        return self.bottom_layout

    def on_slider_value_changed(self, control, value):
        self.out.append(f'Slider value changed for control: {control} to {value}')

    def on_light_selector_changed(self, text):
        self.out.append(f'Light selector changed to {text}')

    def on_selector_changed(self, control, text):
        self.out.append(f'Selector changed for control: {control} to {text}')

    def on_button_clicked(self, control):
        self.bottom_layout.repaint()
        self.out.append(f'Button clicked for control: {control}')



app = QApplication(sys.argv)
window = MainWindow()
blayout=window.getBottomLayout()


window.showMaximized()
sys.exit(app.exec_())
