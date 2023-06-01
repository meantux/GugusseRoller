import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QComboBox, QPushButton, QLineEdit, QTextEdit, QSplitter, QSizePolicy, QWidget, QMessageBox
from PyQt5.QtCore import Qt

from TrinamicSilentMotor import MotorControlWidgets

from GCamera import GCamera
from Lights import LightControlWidget

from picamera2.previews.qt import QGlPicamera2

import CameraSettings
import CaptureSettings

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):        
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("GugusseGUI 2.0")
        
        h=open("GugusseSettings.json","rt")
        self.settings=json.load(h)
        h.close()
        print(json.dumps(self.settings, indent=4))
        fps=self.settings["fps"]
        
        self.picam2=GCamera(self)
        self.picam2.createPreviewWidget()

        
        self.main_layout = QVBoxLayout()

        
        
        self.out = QTextEdit()

        #topWidget=QWidget()
        #top=QHBoxLayout(topWidget)
        #topWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #self.main_layout.addLayout(top)

        
        hlayout=QHBoxLayout()
        
        # Row 1  | Exposure stuff
        self.AutoExposure=CameraSettings.AutoExposureWidget(self)
        hlayout.addWidget(self.AutoExposure.getLabel())
        hlayout.addWidget(self.AutoExposure)
        self.ExposureDual=CameraSettings.ExposureDualWidget(self)
        hlayout.addWidget(self.ExposureDual.getLabel())
        hlayout.addWidget(self.ExposureDual)
        self.Iso=CameraSettings.IsoWidget(self)
        hlayout.addWidget(self.Iso.getLabel())
        hlayout.addWidget(self.Iso)
        self.main_layout.addLayout(hlayout)
        
        hlayout=QHBoxLayout()

        # Row 2 White balance stuff
        self.WBMode=CameraSettings.WhiteBalanceModeWidget(self)
        hlayout.addWidget(self.WBMode.getLabel())
        hlayout.addWidget(self.WBMode)
        self.Freeze=CameraSettings.FreezeWidget(self)
        hlayout.addWidget(self.Freeze)
        self.RedGain=CameraSettings.ColorGainWidget(self, 0)
        hlayout.addWidget(self.RedGain.getLabel())
        hlayout.addWidget(self.RedGain)
        self.BlueGain=CameraSettings.ColorGainWidget(self, 1)
        hlayout.addWidget(self.BlueGain.getLabel())
        hlayout.addWidget(self.BlueGain)
        self.main_layout.addLayout(hlayout)
    
        
        # Bottom section divided into left and right
        self.bottom_layout = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        hlayout=QHBoxLayout()        
        self.vflip=CameraSettings.FlipWidget(self, "vflip")
        self.hflip=CameraSettings.FlipWidget(self, "hflip")
        self.saveSettings=CaptureSettings.SaveSettingsWidget(self)
        hlayout.addWidget(self.hflip)
        hlayout.addWidget(self.vflip)
        hlayout.addWidget(self.saveSettings)
        left_layout.addLayout(hlayout)
        
        
        hlayout=QHBoxLayout()
        self.light_selector = LightControlWidget(self)
        hlayout.addWidget(self.light_selector.getLabel())
        hlayout.addWidget(self.light_selector)
        left_layout.addLayout(hlayout)

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
        self.project_name = CaptureSettings.ProjectNameWidget(self)        
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.project_name.getLabel())
        hlayout.addWidget(self.project_name)
        left_layout.addLayout(hlayout)

        #Capture Mode
        self.filmFormat = CaptureSettings.FilmFormatWidget(self)
        hlayout=QHBoxLayout()
        hlayout.addWidget(self.filmFormat.getLabel())
        hlayout.addWidget(self.filmFormat)
        self.captureMode = CaptureSettings.CaptureModeWidget(self)
        hlayout.addWidget(self.captureMode.getLabel())
        hlayout.addWidget(self.captureMode)
        left_layout.addLayout(hlayout)
        
        #Reels Direction
        self.reelsDirection=CaptureSettings.ReelsDirectionWidget(self)
        hlayout=QHBoxLayout()
        hlayout.addWidget(self.reelsDirection.getLabel())
        hlayout.addWidget(self.reelsDirection)
        left_layout.addLayout(hlayout)

        
        


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
        self.hflip.syncCamera() # syncing one syncs the other, and start cam
        self.picam2.start()

    def disableWidgetsWhenCapture(self):
        self.light_selector.setEnabled(False)
        self.project_name.setEnabled(False)
        self.filmFormat.setEnabled(False)
        self.captureMode.setEnabled(False)

    def reenableWidgetsAfterCapture(self):
        self.light_selector.setEnabled(True)
        self.project_name.setEnabled(True)
        self.filmFormat.setEnabled(True)
        self.captureMode.setEnabled(True)

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

    def closeEvent(self, event):
        if self.saveSettings.thereAreUnsavedSettings():
            reply = QMessageBox.question(self, 'Unsaved Settings', 
                "There are unsaved settings. Do you want to save before exiting?", QMessageBox.Save | 
                QMessageBox.Cancel | QMessageBox.Discard, QMessageBox.Save)

            if reply == QMessageBox.Save:
                # save the work and exit
                self.saveSettings.execute()
                event.accept()
            elif reply == QMessageBox.Discard:
                # discard the work and exit
                event.accept()
            else:
                # cancel the close event
                event.ignore()
        else:
            event.accept()


app = QApplication(sys.argv)
window = MainWindow()
blayout=window.getBottomLayout()


window.showMaximized()
sys.exit(app.exec_())
