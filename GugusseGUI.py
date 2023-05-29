import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QComboBox, QPushButton, QLineEdit, QTextEdit, QSplitter, QSizePolicy, QWidget
from PyQt5.QtCore import Qt

from TrinamicSilentMotor import MotorControlWidgets

from GCamera import GCamera
from Lights import LightControlWidget

from picamera2.previews.qt import QGlPicamera2

import CameraSettings as cs

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("GugusseGUI 2.0")
        
        with open("CameraSettings.json","rt") as h:
            self.settings=json.load(h)
        fps=self.settings["fps"]
        
        self.picam2=GCamera(self)
        self.picam2.createPreviewWidget()

        
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
    
        
        # Bottom section divided into left and right
        self.bottom_layout = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        lights_layout=QHBoxLayout()
        self.light_selector = LightControlWidget(self)
        lights_layout.addWidget(self.light_selector.getLabel())
        lights_layout.addWidget(self.light_selector)
        left_layout.addLayout(lights_layout)

        with open("hardwarecfg.json") as h:
            self.hwSettings=json.load(h)
        
        threeMotorsLayout=QHBoxLayout()
        self.motors={}
        for motor in ["feeder","filmdrive","pickup"]:
            #bordered_widget=QWidget()
            #bordered_widget.setStyleSheet("border: 1px solid black;")            
            motorSeparatorLayout=QVBoxLayout()
            label=QLabel(motor)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid black;")
            motorSeparatorLayout.addWidget(label)
            threeButtonsLayout=QHBoxLayout()
        
            self.motors[motor]=MotorControlWidgets(self, self.hwSettings[motor])
            threeButtonsLayout.addWidget(self.motors[motor].ccw)
            threeButtonsLayout.addWidget(self.motors[motor])
            threeButtonsLayout.addWidget(self.motors[motor].cw)
        
            motorSeparatorLayout.addLayout(threeButtonsLayout)
            threeMotorsLayout.addLayout(motorSeparatorLayout)

        left_layout.addLayout(threeMotorsLayout)
        
        
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
        self.bottom_layout.addWidget(self.picam2.camWidget)

        
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
