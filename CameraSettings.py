from PyQt5.QtWidgets import QSlider, QComboBox, QLabel, QPushButton, QCheckBox
from PyQt5.QtCore import Qt
from libcamera import controls, Transform
from picamera2.previews.qt import QGlPicamera2



defaultValues={
    "Exposure": "Manual",
    "ExposureMicroseconds": 30000,
    "ExposureCompensationStops":0.0,
    "ISO":100,
    "RedGain":"2.1",
    "BlueGain": "2.1",
    "WhileBalanceMode":"Auto"
}


def SetMissingsToDefault(settings):
    for key in defaultValues:
        if key not in settings:
            settings[key]=defaultValues[key]

class AutoExposureWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        self.label=QLabel("Exposure")
        self.addItems(["Manual","CentreWeighted", "Spot", "Matrix"])
        self.win=win
        SetMissingsToDefault(win.settings)
        mode=win.settings["Exposure"]
        self.setCurrentText(mode)
        self.currentTextChanged.connect(self.handle)
        
    def handle(self, text):
        self.syncCamera()

    def syncCamera(self):
        choice=self.currentText()
        self.win.settings["Exposure"]=choice
        if  choice == "Manual":
            self.win.picam2.set_controls({"AeEnable":False})
            self.win.ExposureDual.changeMode()
            self.win.Iso.setEnabled(True)
            self.win.Iso.syncCamera()
        else:
            self.win.picam2.set_controls({"AeEnable":True})
            self.win.ExposureDual.changeMode()
            self.win.Iso.setEnabled(False)
            self.win.ExposureDual.syncCamera()            
        if choice == "CentreWeighted":
            self.win.picam2.set_controls({"AeMeteringMode":controls.AeMeteringModeEnum.CentreWeighted})
        elif choice == "Spot":
            self.win.picam2.set_controls({"AeMeteringMode":controls.AeMeteringModeEnum.Spot})
        elif choice == "Matrix":
            self.win.picam2.set_controls({"AeMeteringMode":controls.AeMeteringModeEnum.CentreWeighted})

    def getLabel(self):
        return self.label
            
            


class previewWindowWidget(QGlPicamera2):
    def __init__(self, win):
        QGlPicamera2.__init__(self, win.picam2)
        self.zoomed=False
        self.win=win

    def mousePressEvent(self, event):
        pos=event.pos()
        x=pos.x()
        y=pos.y()
        winw=self.width()
        winh=self.height()
        sensorw=self.win.picam2.preview_config["main"]["size"][0]
        sensorh=self.win.picam2.preview_config["main"]["size"][1]
        if self.zoomed:
            self.win.picam2.set_controls({"ScalerCrop":(0,0,sensorw,sensorh)})
            self.zoomed=False
            return
        ratioSensor=sensorw/sensorh
        ratioWin=winw/winh
        
        leftBlackPixels=0
        upperBlackPixels=0
        if ratioSensor>ratioWin:
            upperBlackPixels=int((winh-(winw/ratioSensor))/2)
            winh=int(winw/ratioSensor)
        elif ratioSensor<ratioWin:
            leftBlackPixels=int((winw-(winh*ratioSensor))/2)
            winw=int(winh*ratioSensor)            
        
        scalew = sensorw / winw
        scaleh = sensorh / winh
        
        clickx = (x-leftBlackPixels) * scalew
        clicky = (y-upperBlackPixels) * scaleh

        # Make sure the crop doesn't exceed image borders
        x1 = int(max(0, min(clickx - (winw // 2), sensorw - winw)))
        y1 = int(max(0, min(clicky - (winh // 2), sensorh - winh)))

        self.win.picam2.set_controls({"ScalerCrop":(x1,y1,winw,winh)})
        self.zoomed=True






class ExposureDualWidget(QSlider):
    def __init__(self, win):
        QSlider.__init__(self, Qt.Horizontal)
        self.win=win        
        self.label=QLabel(".........")
        
        self.changeMode()
        self.valueChanged.connect(self.handle)
                        
    def changeMode(self):
        exposureMode=self.win.settings["Exposure"]
        if exposureMode=="Manual":
            min=self.win.picam2.video_configuration.controls['FrameDurationLimits'][0]
            max=self.win.picam2.video_configuration.controls['FrameDurationLimits'][1]
            value=self.win.settings["ExposureMicroseconds"]
        else:
            min=int(self.win.picam2.camera_controls["ExposureValue"][0]*2)
            max=int(self.win.picam2.camera_controls["ExposureValue"][1]*2)
            realValue=self.win.settings["ExposureCompensationStops"]
            value=int(realValue * 2.0)
        self.setRange(min, max)
        self.handle(value)        

    def handle(self, value):
        exposureMode=self.win.settings["Exposure"]
        if exposureMode=="Manual":
            self.label.setText(f"{value//1000:4d}ms")
            self.win.settings["ExposureMicroseconds"]=value
        else:
            realValue=float(value)/2.0
            if realValue >= 0.0:
                self.label.setText(f"+{realValue:3.1f} stops")
            else:
                self.label.setText(f"{realValue:4.1f} stops")
            self.win.settings["ExposureCompensationStops"]=realValue
        self.syncCamera()
        self.setValue(value)
            
    def syncCamera(self):
        exposureMode=self.win.settings["Exposure"]
        if exposureMode=="Manual":
            self.win.picam2.set_controls({"ExposureTime":self.value()})
        else:
            realValue=float(self.value())/2.0
            self.win.picam2.set_controls({"ExposureValue":realValue})

    def getLabel(self):
        return self.label


class IsoWidget(QSlider):
    def __init__(self, win):
        QSlider.__init__(self, Qt.Horizontal)
        min=int(win.picam2.camera_controls["AnalogueGain"][0]*100.0)
        max=int(win.picam2.camera_controls["AnalogueGain"][1]*100.0)
        isoValue=win.settings["ISO"]
        self.label=QLabel(f"ISO:{isoValue:5d}")
        self.win=win
        self.setRange(min, max)
        self.setTickInterval(50)
        self.setSingleStep(50)
        self.setValue(isoValue)   
        self.valueChanged.connect(self.handle)
                
    def handle(self, value):
        value=((value+25)//50)*50
        self.setValue(value)
        self.label.setText(f"ISO:{value:5d}")
        self.win.settings["ISO"]=value
        self.setValue(value)
        self.syncCamera()
                
    def syncCamera(self):
        registerValue=float(self.value())/100.0
        self.win.picam2.set_controls({"AnalogueGain":registerValue})

    def getLabel(self):
        return self.label


class ColorGainWidget(QSlider):
    def __init__(self, win, index):
        QSlider.__init__(self, Qt.Horizontal)

        ## min-max hard-coded because of way too much range for nothing.
        #min=int(win.picam2.camera_controls["ColourGains"][0]*1000.0)
        #max=int(win.picam2.camera_controls["ColourGains"][1]*1000.0)
        min=0
        max=5000
        
        self.index=index
        if index==0:
            self.color="Red"
        else:
            self.color="Blue"
        self.win=win
        self.setRange(min, max)
        self.registerValue=self.win.settings[f"{self.color}Gain"]        
        self.label=QLabel(f"{self.color} Gain {self.registerValue:6.3f}")
        sliderValue=int(self.registerValue*1000.0)
        self.setValue(sliderValue)
        self.valueChanged.connect(self.handle)

    def handle(self, value):
        self.registerValue=float(value)/1000.0
        self.label.setText(f"{self.color} Gain {self.registerValue:6.3f}")
        self.win.settings[f"{self.color}Gain"]=self.registerValue
        self.syncCamera()
        
    def syncCamera(self):
        if self.index == 0:
            values=(self.registerValue, self.win.BlueGain.registerValue)
        else:
            values=(self.win.RedGain.registerValue, self.registerValue)
        self.win.picam2.set_controls({"ColourGains":values})

    def getLabel(self):
        return self.label
        
        
        
    
class WhiteBalanceModeWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        self.label=QLabel("WB Mode")
        self.addItems(["Manual","Auto","Tungsten","Fluorescent", "Indoor","Daylight", "Cloudy"])
        self.win=win
        mode=win.settings["WhiteBalanceMode"]
        self.setCurrentText(mode)
        self.currentTextChanged.connect(self.handle)

    def handle(self, text):
        if text != self.currentText():
            self.setCurrentText(text)
        self.syncCamera()

    def syncCamera(self):
        choice=self.currentText()
        self.win.settings["WhiteBalanceMode"]=choice
        if choice == "Manual":
            self.win.picam2.set_controls({"AwbEnable":False})
            self.win.Freeze.setEnabled(False)
            self.win.RedGain.setEnabled(True)
            self.win.BlueGain.setEnabled(True)
            self.win.RedGain.syncCamera()
        else:
            self.win.picam2.set_controls({"AwbEnable":True})
            self.win.Freeze.setEnabled(True)
            self.win.RedGain.setEnabled(False)
            self.win.BlueGain.setEnabled(False)            
            if choice=="Auto":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Auto})
            elif choice=="Tungsten":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Tungsten})
            elif choice=="Fluorescent":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Fluorescent})
            elif choice=="Indoor":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Indoor})
            elif choice=="Daylight":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Daylight})
            elif choice=="Cloudy":
                self.win.picam2.set_controls({"AwbMode":controls.AwbModeEnum.Cloudy})        

    def getLabel(self):
        return self.label
            

class FreezeWidget(QPushButton):
    def __init__(self, win):
        QPushButton.__init__(self, "Freeze")
        self.win=win
        self.setEnabled(False) # Will be enable if WB's not Manual
        self.clicked.connect(self.handle)
        self.win.picam2.camWidget.done_signal.connect(self.handleMetadata)
        
    def handle(self):
        self.setEnabled(False)
        self.win.picam2.capture_metadata(signal_function=self.win.picam2.camWidget.signal_done)

    def handleMetadata(self, job):
        metadata=self.win.picam2.wait(job)        
        newValues=metadata["ColourGains"]
        self.win.RedGain.setValue(int(newValues[0]*1000.0))
        self.win.BlueGain.setValue(int(newValues[1]*1000.0))
        self.win.settings["RedGain"]=newValues[0]
        self.win.settings["BlueGain"]=newValues[1]
        self.win.WBMode.handle("Manual")

class FlipWidget(QCheckBox):
    def __init__(self, win, which):
        QCheckBox.__init__(self, which)
        self.win=win
        self.which=which
        if which in self.win.settings:
            current=self.win.settings[which]
            self.setChecked(current)            
        else:
            self.setChecked(False)
            self.win.settings[which]=False                
        self.stateChanged.connect(self.handle)
        
    def handle(self):        
        self.win.settings[self.which]=self.isChecked()
        self.win.out.append("Change requires save and restart")
        self.syncCamera()

    def syncCamera(self):
        pass
        # we don't know how to do that yet.
    
