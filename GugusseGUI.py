import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QComboBox, QPushButton, QLineEdit, QTextEdit, QSplitter, QSizePolicy, QWidget, QMessageBox
from PyQt5.QtCore import Qt

from TrinamicSilentMotor import MotorControlWidgets

from GCamera import GCamera
from Lights import LightControlWidget

import CameraSettings
import CaptureSettings
import CaptureLoop
import SensorReport
from ConfigFiles import ConfigFiles

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):        
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("GugusseGUI 2.0")
        self.settings=ConfigFiles("GugusseSettings.json")
        print(json.dumps(self.settings, indent=4))
        fps=self.settings["fps"]
        
        self.picam2=GCamera(self)
        self.picam2.createPreviewWidget()
        self.main_layout = QVBoxLayout()        
        self.out = QTextEdit()


        print("--------Available Camera Settings------")
        print(json.dumps(self.picam2.camera_controls, indent=4))
        print("---------------------------------------")
        
        #topWidget=QWidget()
        #top=QHBoxLayout(topWidget)
        #topWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #self.main_layout.addLayout(top)

        
        hlayout=QHBoxLayout()
        
        # Row 1:  | Exposure stuff
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

        # Row 2: White balance stuff
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

        hlayout=QHBoxLayout()
        # Row 3: Post-processing adjustments
        self.brightness=CameraSettings.GenericCameraAdjustmentWidget(self, "Brightness", customMin= -0.5, customMax= 0.5)
        hlayout.addWidget(self.brightness.getLabel())
        hlayout.addWidget(self.brightness)
        self.contrast=CameraSettings.GenericCameraAdjustmentWidget(self, "Contrast", customMax=2.00)
        hlayout.addWidget(self.contrast.getLabel())
        hlayout.addWidget(self.contrast)
        self.sharpness=CameraSettings.GenericCameraAdjustmentWidget(self, "Sharpness", customMax=10.0)
        hlayout.addWidget(self.sharpness.getLabel())
        hlayout.addWidget(self.sharpness)
        self.saturation=CameraSettings.GenericCameraAdjustmentWidget(self, "Saturation", customMin=0.01,customMax=1.99)
        hlayout.addWidget(self.saturation.getLabel())
        hlayout.addWidget(self.saturation)
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

        self.hwSettings=ConfigFiles("hardwarecfg.json")
        
        threeMotorsLayout=QHBoxLayout()
        self.motors={}
        for motor in ["feeder","filmdrive","pickup"]:
            motorSeparatorLayout=QVBoxLayout()
            label=QLabel(motor)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid black;")
            motorSeparatorLayout.addWidget(label)
            threeButtonsLayout=QHBoxLayout()
            trace=False
            #if motor == "filmdrive":
            #    trace=True
            #else:
            #    trace=False
            self.motors[motor]=MotorControlWidgets(self, self.hwSettings[motor], trace=trace)
            threeButtonsLayout.addWidget(self.motors[motor].ccw)
            threeButtonsLayout.addWidget(self.motors[motor])
            threeButtonsLayout.addWidget(self.motors[motor].cw)
        
            motorSeparatorLayout.addLayout(threeButtonsLayout)
            threeMotorsLayout.addLayout(motorSeparatorLayout)

        left_layout.addLayout(threeMotorsLayout)
        
        
        # Project name field
        self.projectName = CaptureSettings.ProjectNameWidget(self)        
        hlayout = QHBoxLayout()
        self.light_selector = LightControlWidget(self)
        hlayout.addWidget(self.light_selector.getLabel())
        hlayout.addWidget(self.light_selector)
        left_layout.addLayout(hlayout)

        hlayout.addWidget(self.projectName.getLabel())
        hlayout.addWidget(self.projectName)
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

        #Run/Stop + Take Picture
        self.runStop=CaptureLoop.RunStopWidget(self)
        self.snapshot=CaptureLoop.SnapshotWidget(self)        
        hlayout=QHBoxLayout()
        hlayout.addWidget(self.snapshot)
        hlayout.addWidget(self.runStop)
        left_layout.addLayout(hlayout)
        self.sensors=SensorReport.SensorsWidgets(self)
        left_layout.addLayout(self.sensors)
        
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
        self.brightness.syncCamera()
        self.contrast.syncCamera()
        self.saturation.syncCamera()
        self.sharpness.syncCamera()
        self.hflip.syncCamera() # syncing one syncs the other, and start cam
        self.picam2.start()

    def disableWidgetsWhenCapture(self):
        self.light_selector.setEnabled(False)
        self.projectName.setEnabled(False)
        self.filmFormat.setEnabled(False)
        self.captureMode.setEnabled(False)
        self.sensors.learn.setEnabled(False)
        self.snapshot.setEnabled(False)

    def reenableWidgetsAfterCapture(self):
        self.light_selector.setEnabled(True)
        self.projectName.setEnabled(True)
        self.filmFormat.setEnabled(True)
        self.captureMode.setEnabled(True)
        self.snapshot.setEnabled(True)
        self.sensors.enableLearnIfPossible()
        self.motors["feeder"].syncMotorStatus()
        self.motors["filmdrive"].syncMotorStatus()
        self.motors["pickup"].syncMotorStatus()
        

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
                self.snapshot.disableExportIfRunning()
                event.accept()
            elif reply == QMessageBox.Discard:
                # discard the work and exit
                self.snapshot.disableExportIfRunning()
                event.accept()
            else:
                # cancel the close event
                event.ignore()
        else:
            self.snapshot.disableExportIfRunning()
            event.accept()


app = QApplication(sys.argv)
window = MainWindow()
blayout=window.getBottomLayout()


window.showMaximized()
sys.exit(app.exec_())
