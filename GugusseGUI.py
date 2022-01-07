#!/usr/bin/python3
from tkinter import *
from json import load,dump,dumps
from GCamera import GCamera
from CaptureLoop import CaptureLoop
from time import sleep
from datetime import datetime
from math import sqrt
import RPi.GPIO as GPIO
from TrinamicSilentMotor import TrinamicSilentMotor
from SensorReport import SensorReport
from Lights import Lights
GPIO.setmode(GPIO.BCM)
light=Lights("on")
sensors=None
root= Tk()

scr_w = root.winfo_screenwidth()
scr_h = root.winfo_screenheight()

borderwidth=1
if scr_w <= 600:
    borderwidth=0
if scr_w > 720:
    borderwidth=2

widget_h=4
widget_wchars=13
widget_w=widget_wchars*12
top_h=180
left_w=2*widget_w

CaptureBG=None


cam=GCamera()
root.attributes("-fullscreen",True)

topFrame=Frame(root, highlightbackground="black", highlightthickness=1)
topFrame.pack(side="top",fill="both")
leftFrame=Frame(root, highlightbackground="black", highlightthickness=1)
leftFrame.pack(side="left",fill="both")
previewSize=(scr_w-left_w,scr_h-top_h)
picFrame=Frame(root, width=previewSize[0],height=previewSize[1])
picFrame.pack(side="right",fill="both")
topLabel=Label(topFrame,text="Gugusse Roller")
topLabel.pack(side="top")

capture=None


settingsDefaults={
    "awb_gains": [
        3.0,
        2.0
    ],
    "awb_mode": "auto",
    "brightness": 50,
    "captureMode": "PyDNG",
    "contrast": 0,
    "exposure_compensation": 0,
    "exposure_mode": "auto",
    "filmFormat": "35mm",
    "hflip": False,
    "image_effect": "none",
    "iso": 100,
    "direction": "cw",
    "saturation": 0,
    "sharpness": 0,
    "shutter_speed": 24000,
    "vflip": False    
}
settings=dict(settingsDefaults)


with open("GugusseSettings.json","rt") as h:
    settingsFromFile=load(h)
    h.close()
    for item in settingsFromFile:
        settings[item]=settingsFromFile[item]

with open("captureModes.json","rt") as h:
    captureModesDetails=load(h)
    h.close()

captureModesList=[]
for item in captureModesDetails:
    captureModesList.append(str(item))
    
with open("hardwarecfg.json","rt") as h:
    hardware=load(h)
    for item in hardware:
        settings[item]=hardware[item]
    h.close()



    
def previewHandle():
    if previewHandle.running:
        previewButton.configure(text="Preview On")
        cam.stop_preview();
        previewHandle.running=False
    else:
        previewHandle.running=True
        previewButton.configure(text="Preview Off")
        start_preview(settings["hflip"],settings["vflip"])
previewHandle.running=True
        
def start_preview(hflip, vflip):
    global widget_w
    global top_h
    global scr_w
    global scr_h
    global previewHandle
    px=2*widget_w
    py=top_h
    pw=scr_w-px
    ph=scr_h-py
    if previewHandle.running:
        cam.start_preview(fullscreen=False,resolution=(2880,2160),window=(px,py,pw,ph),hflip=hflip,vflip=vflip)

start_preview(settings["hflip"],settings["vflip"])

captureMode=StringVar(root)
captureMode.set(settings["captureMode"])

filmFormat=StringVar(root)
filmFormat.set(settings["filmFormat"])

exposureMode=StringVar(root)
exposureMode.set(settings["exposure_mode"])

#meterMode=StringVar(root)
#meterMode.set(settings["meter_mode"])
#cam.meter_mode=settings["meter_mode"]

awbMode=StringVar(root)
awbMode.set(settings["awb_mode"])
cam.awb_mode=settings["awb_mode"]

imageEffect=StringVar(root)
imageEffect.set(settings["image_effect"])
cam.image_effect=settings["image_effect"]

direction=StringVar(root)
direction.set(settings["direction"])

projectName=StringVar(root)
projectName.set(datetime.now().strftime("%Y%m%d-%H%M"))

color=StringVar(root)
color.set("on")

def messagePrint(txt):
    print(txt)
    message3.configure(text=messagePrint.text3)
    message2.configure(text=messagePrint.text2)
    message1.configure(text=messagePrint.text1)
    message.configure(text=txt)    
    messagePrint.text3=messagePrint.text2
    messagePrint.text2=messagePrint.text1
    messagePrint.text1=txt
messagePrint.text3=""
messagePrint.text2=""
messagePrint.text1=""


    
def filterProjectName():
    prj=prjBox.get()
    newprj=""
    for aChar in prj:
        if aChar in "-+_:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            newprj="{}{}".format(newprj, aChar)
        else:
            newprj="{}_".format(newprj)
    if prj != newprj:
        prjBox.set(newprj)
        messagePrint("project name filtered")

def saveSettings():
    if saveSettings.settingsChanged == False:
        messagePrint("No change to save")
        return
    tosave={}
    for item in settingsDefaults:
        tosave[item]=settings[item]
    with open("GugusseSettings.json","wt") as h:
        messagePrint("Saving Settings")
        dump(tosave,h,sort_keys=True, indent=4)
        h.close()
        messagePrint("Settings Saved")
        saveSettings.settingsChanged=False

def handleLightChange(event):
    light.set(event)
    color.set(event)
    if event == "off":
        lightSelector.configure(bg="black",fg="white")
    elif event == "on":
        lightSelector.configure(bg="white",fg="black")
    elif event == "blue":
        lightSelector.configure(bg="blue", fg="yellow")
    else:
        lightSelector.configure(bg=event, fg="black")

        
def handleExposureChange(event):
    if exposureMode.get() == "off":
        settings["shutter_speed"]=int(event)
        cam.shutter_speed=int(event)
    saveSettings.settingsChanged=True
        
def handleWbGain1(event):    
    settings["awb_gains"][0]=float(event)
    cam.awb_gains=settings["awb_gains"]
    saveSettings.settingsChanged=True

def handleWbGain2(event):
    settings["awb_gains"][1]=float(event)
    cam.awb_gains=settings["awb_gains"]
    saveSettings.settingsChanged=True

def handleImageEffectChange(event):
    val=str(event)
    settings["image_effect"]=val
    cam.image_effect=val
    saveSettings.settingsChanged=True

def handleBrightnessChange(event):
    val=int(event)
    settings["brightness"]=val
    cam.brightness=val
    saveSettings.settingsChanged=True

def handleContrastChange(event):
    val=int(event)
    settings["contrast"]=val
    cam.contrast=val
    saveSettings.settingsChanged=True

def handleFilmFormatChange(event):
    val=str(event)
    filmFormat.set(event)
    settings["filmFormat"]=val
    saveSettings.settingsChanged=True

def handleCaptureModeChange(event):
    val=str(event)    
    settings["captureMode"]=val
    captureMode.set(event)
    saveSettings.settingsChanged=True
    cam.changeCaptureMode(val)
    
def handleAwbModeChange(event):
    val=str(event)
    settings["awb_mode"]=val
    if val == "off":
        wbGain1.configure(state="normal",fg="black")
        wbGain2.configure(state="normal",fg="black")        
    else:
        wbGain1.configure(state="disabled",fg="grey")
        wbGain2.configure(state="disabled",fg="grey")
    cam.awb_mode=val
    awbMode.set(val)
    saveSettings.settingsChanged=True

def handleExposureModeChange(event):
    val=str(event)
    settings["exposure_mode"]=val
    exposureMode.set(val)
    if val == "off":
        exposition.configure(state="normal",fg="black")
        compensation.configure(state="disabled",fg="gray")
        iso.configure(state="disabled",fg="gray")
        if handleExposureModeChange.ExposureWasNotOff:            
            cam.shutter_speed=exposition.get()
            handleExposureModeChange.ExposureWasNotOff=False
    else:
        iso.configure(state="normal",fg="black")
        compensation.configure(state="normal",fg="black")
        cam.shutter_speed=0
        exposition.configure(state="disabled",fg="gray")
        handleExposureModeChange.ExposureWasNotOff=True
    cam.exposure_mode=val
    saveSettings.settingsChanged=True

def handleSaturationChange(event):
    val=int(event)
    cam.saturation=val
    settings["saturation"]=val
    saveSettings.settingsChanged=True

def handleSharpnessChange(event):
    val=int(event)
    cam.sharpness=val
    settings["saturation"]=val
    saveSettings.settingsChanged=True

def handleIsoChange(event):
    val=int(event)
    settings["iso"]=val
    cam.iso=val
    saveSettings.settingsChanged=True

def handleCompensationChange(event):
    val=int(event)
    settings["compensation"]=val
    cam.exposure_compensation=val
    saveSettings.settingsChanged=True

def handleDirectionChange(event):
    val=str(event)
    direction.set(val)
    settings["direction"]=val
    saveSettings.settingsChanged=True

def handleHFlip():
    val= not settings["hflip"]
    settings["hflip"]=val    
    if previewHandle.running:
        cam.stop_preview()
    sleep (0.1)
    start_preview(val, settings["vflip"])
    saveSettings.settingsChanged=True
    
def handleVFlip():
    val= not settings["vflip"]
    settings["vflip"]=val
    if previewHandle.running:
        cam.stop_preview()
    sleep (0.1)
    start_preview(settings["hflip"], val)
    saveSettings.settingsChanged=True

    
def pwrMotor(name):
    global motors
    global powers
    val=motors[name].getPowerState()
    if val:
        motors[name].enable()
    else:
        motors[name].disable()

def advMotor(name,direction):
    motors[name].setDirection(direction)
    motors[name].blindMove(1000)

def handlePickupCw():
    advMotor("pickup","cw")

def handlePickupCcw():
    advMotor("pickup","ccw")

def handlePickupPwr():
    pwrMotor("pickup")

def handleMainDriveCw():
    advMotor("filmdrive","cw")

def handleMainDriveCcw():
    advMotor("filmdrive","ccw")
    pass

def handleMainDrivePwr():
    pwrMotor("filmdrive")
    pass

def handleFeederCw():
    advMotor("feeder","cw")
    pass

def handleFeederCcw():
    advMotor("feeder","ccw")
    pass

def handleFeederPwr():
    pwrMotor("feeder")
    pass


def runHandle():
    global CaptureBG
    global motors
    if runHandle.running:
        runButton.configure(text="Run",state="disabled",fg="grey")
        runHandle.running=False
        if CaptureBG!=None:
            CaptureBG.stopLoop()
    else:
        if runHandle.clean == False:
            CaptureBG.join()
            runHandle.clean=True
        filterProjectName()
        if prjBox.get()=="":            
            messagePrint("You need to set a project name")
            return
        captureModeSelector.configure(state="disabled",fg="grey")
        runButton.configure(text="Stop")
        runHandle.running=True
        prjBox.configure(state="disabled")
        prjLbl.configure(fg="grey")
        uiTools={
            "captureModeSelector":captureModeSelector,
            "handleLightChange":handleLightChange,
            "runButton": runButton,
            "message": messagePrint,
            "runHandle": runHandle,
            "prjBox":prjBox
        }        
        for name in motors.keys():
            motors[name].setFormat(settings["filmFormats"][filmFormat.get()][name])
        CaptureBG=CaptureLoop(cam, motors, settings, prjBox.get(),uiTools)
        CaptureBG.start()
runHandle.running=False
runHandle.clean=True

def handlePrjNameChange(event):
    print(event)


handleExposureModeChange.ExposureWasNotOff=False



miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
###### SATURATION SCALE
saturation=Scale(miniFrame,from_= -100,to=100,length=int(scr_w/2-widget_w),width=8,resolution=1,orient=HORIZONTAL,command=handleSaturationChange)
saturation.set(settings["saturation"])
saturation.pack(side="right")
Label(miniFrame, text="Saturation:",width=widget_wchars,anchor="e").pack(side="right")
###### SHARPNESS SCALE
sharpness=Scale(miniFrame,from_= -100,to=100,length=int(scr_w/2-widget_w),width=8,resolution=1,orient=HORIZONTAL,command=handleSharpnessChange)
sharpness.set(settings["sharpness"])
sharpness.pack(side="right")
Label(miniFrame, text="Sharpness:").pack(side="right")

miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
###### WBGAIN2 SCALE
wbGain2=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL,command=handleWbGain2)
wbGain2.set(settings["awb_gains"][1])
wbGain2.pack(side="right")
Label(miniFrame,text="      WB Gain 2:",width=widget_wchars,anchor="e").pack(side="right")
####### WBGAIN1 SCALE
wbGain1=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL,command=handleWbGain1)
wbGain1.set(settings["awb_gains"][0])
wbGain1.pack(side="right")
Label(miniFrame,text="WB Gain 1:").pack(side="right")

miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
####### CONTRAST SCALE
contrast=Scale(miniFrame,from_= -100,to=100,length=int(scr_w/2-widget_w),width=8,resolution=1,orient=HORIZONTAL,command=handleContrastChange)
contrast.set(settings["contrast"])
contrast.pack(side="right")
Label(miniFrame,text="Contrast:",width=widget_wchars,anchor="e").pack(side="right")
###### EXPOSITION SCALE
exposition=Scale(miniFrame,from_=1,to=32700,resolution=100,length=scr_w/2-widget_w,width=8,orient=HORIZONTAL,command=handleExposureChange)
exposition.set(settings["shutter_speed"])
exposition.pack(side="right")
Label(miniFrame,text="Exposure:",width=widget_wchars,anchor="e").pack(side="right")

miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
###### BRIGHTNESS SCALE
brightness=Scale(miniFrame,from_=0,to=100,length=int(scr_w/3-widget_w),width=8,resolution=1,orient=HORIZONTAL,command=handleBrightnessChange)
brightness.set(settings["brightness"])
brightness.pack(side="right")
Label(miniFrame,text="Brightness:",width=widget_wchars,anchor="e").pack(side="right")
###### ISO SCALE
iso=Scale(miniFrame,from_=100,to=800,resolution=100,length=scr_w/4-widget_w,width=8,orient=HORIZONTAL,command=handleIsoChange)
iso.set(settings["iso"])
iso.pack(side="right")
Label(miniFrame,text="Iso:",width=widget_wchars,anchor="e").pack(side="right")
###### AUTO-EXPOSURE COMPENSATION SCALE
compensation=Scale(miniFrame,from_= -25,to=25,resolution=1,length=scr_w/3-widget_w,width=8,orient=HORIZONTAL,command=handleCompensationChange)
compensation.set(settings["exposure_compensation"])
compensation.pack(side="right")
Label(miniFrame,text="Auto Compensate:").pack(side="right")
lightSelector=OptionMenu(miniFrame, color, *light.getOptions(), command=handleLightChange)
lightSelector.pack(side="right")
lightSelector.configure(width=widget_wchars, bg="white")
Label(miniFrame, text="Light:").pack(side="right")

###### Film Format
miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
filmFormatSelector=OptionMenu(miniFrame,filmFormat,*settings["filmFormats"],command=handleFilmFormatChange)
filmFormatSelector.config(width=widget_wchars, borderwidth=borderwidth)
filmFormatSelector.pack(side="right")
lbl=Label(miniFrame,text="Film format:",width=widget_wchars,anchor="e")
lbl.pack(side="right")
###### Capture Mode
miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
captureModeSelector=OptionMenu(miniFrame,captureMode,*captureModesList,command=handleCaptureModeChange)
captureModeSelector.config(width=widget_wchars, borderwidth=borderwidth)
captureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Capture Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")
##### Exposure Mode
miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
exposureModeSelector=OptionMenu(miniFrame,exposureMode,*cam.EXPOSURE_MODES.keys(),command=handleExposureModeChange)
exposureModeSelector.config(width=widget_wchars, borderwidth=borderwidth)
exposureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Exposure Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
awbModeSelector=OptionMenu(miniFrame,awbMode,*cam.AWB_MODES.keys(),command=handleAwbModeChange)
awbModeSelector.config(width=widget_wchars, borderwidth=borderwidth)
awbModeSelector.pack(side="right")
lbl=Label(miniFrame,text="AWB Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
imageEffectSelector=OptionMenu(miniFrame,imageEffect,*cam.IMAGE_EFFECTS,command=handleImageEffectChange)
imageEffectSelector.config(width=widget_wchars, borderwidth=borderwidth)
imageEffectSelector.pack(side="right")
lbl=Label(miniFrame,text="ImageEffect:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
possibleDirections=("cw","ccw")
directionSelector=OptionMenu(miniFrame,direction,*possibleDirections,command=handleDirectionChange)
directionSelector.config(width=widget_wchars, borderwidth=borderwidth)
directionSelector.pack(side="right")
lbl=Label(miniFrame,text="Reels Direction:",width=widget_wchars,anchor="e")
lbl.pack(side="right")



miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
SaveButton=Button(miniFrame, text="Save Settings", width=widget_wchars, command=saveSettings)
SaveButton.pack(side="right")
vflipButton=Button(miniFrame, text="vflip",command=handleVFlip)
vflipButton.pack(side="right")
hflipButton=Button(miniFrame, text="hflip",command=handleHFlip)
hflipButton.pack(side="right")


miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
runButton=Button(miniFrame, text="Run", width=widget_wchars, command=runHandle)
runButton.pack(side="right")

previewButton=Button(miniFrame, text="Preview Off", width=widget_wchars, command=previewHandle)
previewButton.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
prjLbl=Label(miniFrame,text="Project name",width=widget_wchars)
prjLbl.pack(side="top")
prjBox=Entry(miniFrame,textvariable=projectName)
prjBox.pack()


Label(leftFrame, text="Feeder    |  MainDrive  |    Pickup ").pack(side="top")
cwPic=PhotoImage(file="cw.png")
ccwPic=PhotoImage(file="ccw.png")
powerPic=PhotoImage(file="power.png")
miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
pickupCwButton=Button(miniFrame,image=cwPic,command=handlePickupCw)
pickupCwButton.pack(side="right")
pickupPwrButton=Button(miniFrame,image=powerPic,command=handlePickupPwr)
pickupPwrButton.pack(side="right")
pickupCcwButton=Button(miniFrame,image=ccwPic,command=handlePickupCcw)
pickupCcwButton.pack(side="right")

mainDriveCwButton=Button(miniFrame,image=cwPic,command=handleMainDriveCw)
mainDriveCwButton.pack(side="right")
mainDrivePwrButton=Button(miniFrame,image=powerPic,command=handleMainDrivePwr)
mainDrivePwrButton.pack(side="right")
mainDriveCcwButton=Button(miniFrame,image=ccwPic,command=handleMainDriveCcw)
mainDriveCcwButton.pack(side="right")

feederCwButton=Button(miniFrame,image=cwPic,command=handleFeederCw)
feederCwButton.pack(side="right")
feederPwrButton=Button(miniFrame,image=powerPic,command=handleFeederPwr)
feederPwrButton.pack(side="right")
feederCcwButton=Button(miniFrame,image=ccwPic,command=handleFeederCcw)
feederCcwButton.pack(side="right")

def handleLearn():
    # Hack! using prjBox state as it reflects if we're capturing or not.
    if prjBox["state"]=="disabled":
        messagePrint("not while capturing")
    else:
        sensors.toggleLearn()


sensorFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
def handleSensors():
    global sensors
    if handleSensors.running:
        sensors.stopLoop()
        sensors.join()
        sensorsButton.configure(bg="black", fg="white")
        RDetector.configure(bg="grey", fg="grey")
        LDetector.configure(bg="grey", fg="grey")
        HDetector.configure(bg="grey", fg="grey")
        LearnButton.configure(state="disabled",bg="grey",fg="grey")
        handleSensors.running=False
    else:
        
        sensors=SensorReport(settings, LDetector, HDetector, RDetector, LearnButton)
        sensors.start()
        sensorsButton.configure(bg="white", fg="black")
        LearnButton.configure(state="normal")
        handleSensors.running=True
handleSensors.running=False

sensorFrame.pack(side="top",fill="x")
RDetector=Label(sensorFrame,text="R", width=1,fg="grey", bg="grey")
RDetector.pack(side="right")
HDetector=Label(sensorFrame,text="H", width=1,fg="grey", bg="grey")
HDetector.pack(side="right")
LDetector=Label(sensorFrame,text="L", width=1,fg="grey", bg="grey")
LDetector.pack(side="right")
LearnButton=Button(sensorFrame,text="learn",command=handleLearn,state="disabled")
LearnButton.pack(side="right")
sensorsButton=Button(sensorFrame, text="Monitoring Sensors", command=handleSensors)
sensorsButton.pack(side="right")
sensorsButton.configure(bg="black", fg="white")





message3=Label(leftFrame,text="",anchor="e",width=2*widget_wchars)
message3.pack(side="top")

message2=Label(leftFrame,text="",anchor="e",width=2*widget_wchars)
message2.pack(side="top")

message1=Label(leftFrame,text="",anchor="e",width=2*widget_wchars)
message1.pack(side="top")

message=Label(leftFrame,text="",anchor="e",width=2*widget_wchars)
message.pack(side="top")

powers={
    "feeder": feederPwrButton,
    "filmdrive": mainDrivePwrButton,
    "pickup":pickupPwrButton
}
motors={
    "feeder": TrinamicSilentMotor(settings["feeder"],slowEnd=False,button=powers["feeder"], msg=messagePrint),
    "pickup": TrinamicSilentMotor(settings["pickup"],slowEnd=False,button=powers["pickup"], msg=messagePrint),
    "filmdrive": TrinamicSilentMotor(settings["filmdrive"], slowEnd=True,trace=True,button=powers["filmdrive"], msg=messagePrint)
}
for item in motors:
    if motors[item].getPowerState==0:
        powers[item].configure(bg="grey")
    else:
        powers[item].configure(bg="green")


handleAwbModeChange(awbMode.get())
handleExposureModeChange(exposureMode.get())

saveSettings.settingsChanged=False
def click_handler(event):
    global previewSize
    step=sqrt(2.0)
    zoomLimit=16
    z=click_handler.zoom
    oldfactor=1.0/(z[2]-z[0])
    if settings["hflip"]:
        flippedX=previewSize[0]-event.x
    else:
        flippedX=event.x
    if settings["vflip"]:
        flippedY=previewSize[1]-event.y
    else:
        flippedY=event.y    
    if event.num == 3:
        # reset zoom
        click_handler.zoom=(0.0,0.0,1.0,1.0)
        cam.zoom=click_handler.zoom
        messagePrint("zoom factor: 1.00")
        messagePrint("zoom (0.000,0.000,1.000,1.000)")
    elif event.num == 1:
        # ZOOM IN FULL
        if oldfactor >= zoomLimit:
            return
        factor=zoomLimit
        maxXY=1.0-(1/factor)
        posX=float(flippedX)/float(previewSize[0])
        newX=z[0]+posX/oldfactor-(0.5/factor)
        if newX < 0.0:
            newX = 0.0
        if newX > maxXY:
            newX=maxXY
        posY=float(flippedY)/float(previewSize[1])
        newY=z[1]+posY/oldfactor-(0.5/factor)
        if newY < 0.0:
            newY = 0.0
        if newY > maxXY:
            newY=maxXY
        newXb=newX+(1.0/factor)
        newYb=newY+(1.0/factor)
        z=(newX,newY,newXb,newYb)
        cam.zoom=z
        click_handler.zoom=z
        messagePrint("zoom factor: {:.2f}".format(factor))
        messagePrint("zoom ({:.3f},{:.3f},{:.3f},{:.3f})".format(newX,newY,newXb,newYb))
    elif event.num == 4:
        # ZOOM IN
        if oldfactor >= zoomLimit:
            return
        factor=step*oldfactor
        if factor > zoomLimit:
            factor=zoomLimit
        maxXY=1.0-(1/factor)
        posX=float(flippedX)/float(previewSize[0])
        newX=z[0]+posX/oldfactor-(0.5/factor)
        if newX < 0.0:
            newX = 0.0
        if newX > maxXY:
            newX=maxXY
        posY=float(flippedY)/float(previewSize[1])
        newY=z[1]+posY/oldfactor-(0.5/factor)
        if newY < 0.0:
            newY = 0.0
        if newY > maxXY:
            newY=maxXY
        newXb=newX+(1.0/factor)
        newYb=newY+(1.0/factor)
        z=(newX,newY,newXb,newYb)
        cam.zoom=z
        click_handler.zoom=z
        messagePrint("zoom factor: {:.2f}".format(factor))
        messagePrint("zoom ({:.3f},{:.3f},{:.3f},{:.3f})".format(newX,newY,newXb,newYb))
    elif event.num == 5:
        # ZOOM OUT
        if oldfactor < 0.0000001:
            return
        factor=oldfactor/step
        if factor < 1.0:
            factor=1.0
        maxXY=1.0-(1/factor)
        posX=float(flippedX)/float(previewSize[0])
        newX=z[0]+posX/oldfactor-(0.5/factor)
        if newX < 0.0:
            newX = 0.0
        if newX > maxXY:
            newX=maxXY
        posY=float(flippedY)/float(previewSize[1])
        newY=z[1]+posY/oldfactor-(0.5/factor)
        if newY < 0.0:
            newY = 0.0
        if newY > maxXY:
            newY=maxXY
        newXb=newX+(1.0/factor)
        newYb=newY+(1.0/factor)
        z=(newX,newY,newXb,newYb)
        cam.zoom=z
        click_handler.zoom=z
        messagePrint("zoom factor: {:.2f}".format(factor))
        messagePrint("zoom ({:.3f},{:.3f},{:.3f},{:.3f})".format(newX,newY,newXb,newYb))
        
            
click_handler.zoom=(0.0,0.0,1.0,1.0)    
    
picFrame.bind("<Button>",click_handler)


root.mainloop()
if handleSensors.running:
    sensors.stopLoop()
    sensors.join()
