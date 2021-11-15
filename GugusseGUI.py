#!/usr/bin/python3
from tkinter import *
from json import load,dump
from GCamera import GCamera
from time import sleep
from math import sqrt
#from PreviewGUI import PreviewGUI


root= Tk()

scr_w = root.winfo_screenwidth()
scr_h = root.winfo_screenheight()
widget_h=4
widget_wchars=14
widget_w=widget_wchars*10
top_h=180
left_w=2*widget_w




cam=GCamera()
px=2*widget_w
py=top_h
pw=scr_w-px
ph=scr_h-py
cam.start_preview(fullscreen=False,resolution=(2880,2160),window=(px,py,pw,ph),vflip=False,hflip=False)
root.attributes("-fullscreen",True)

topFrame=Frame(root, highlightbackground="black", highlightthickness=1)
topFrame.pack(side="top",fill="both")
leftFrame=Frame(root, highlightbackground="black", highlightthickness=1)
leftFrame.pack(side="left",fill="both")
previewSize=(scr_w-left_w,scr_h-top_h)
picFrame=Frame(root, width=previewSize[0],height=previewSize[1])
picFrame.pack(side="right",fill="both")
#canvas=Canvas(picFrame,width=scr_w-left_w,height=scr_h-top_h)
#canvas.pack()
#preview=PreviewGUI(cam,canvas,previewSize)
topLabel=Label(topFrame,text="Gugusse Roller")
topLabel.pack(side="top")


settings={
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
    "image_effect": "none",
    "iso": 100,
    "meter_mode": "average",
    "raw_format": "yuv",
    "direction": "cw",
    "saturation": 0,
    "sharpness": 0,
    "shutter_speed": 24000
}
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

with open("filmFormats.json","rt") as h:
    filmFormatsDetails=load(h)
    h.close()

filmFormatsList=[]
for item in filmFormatsDetails:
    filmFormatsList.append(str(item))
    
captureMode=StringVar(root)
captureMode.set(settings["captureMode"])

filmFormat=StringVar(root)
filmFormat.set(settings["filmFormat"])

exposureMode=StringVar(root)
exposureMode.set(settings["exposure_mode"])

meterMode=StringVar(root)
meterMode.set(settings["meter_mode"])
cam.meter_mode=settings["meter_mode"]

awbMode=StringVar(root)
awbMode.set(settings["awb_mode"])
cam.awb_mode=settings["awb_mode"]

imageEffect=StringVar(root)
imageEffect.set(settings["image_effect"])
cam.image_effect=settings["image_effect"]

rawFormat=StringVar(root)
rawFormat.set(settings["raw_format"])
cam.raw_format=settings["raw_format"]

direction=StringVar(root)
direction.set(settings["direction"])

def saveSettings():
    if saveSettings.settingsChanged == False:
        message.configure(text="No change to save")
        return
    with open("GugusseSettings.json","wt") as h:
        message.configure(text="Saving Settings")
        dump(settings,h,sort_keys=True, indent=4)
        h.close()
        message.configure(text="Settings Saved")
        saveSettings.settingsChanged=False


def handleExposureChange(event):
    if exposureMode.get() == "off":
        settings["shutter_speed"]=int(event)
        cam.shutter_speed=int(event)
    saveSettings.settingsChanged=True
        
def handleMeterModeChange(event):
    val=str(event)
    settings["meter_mode"]=val
    cam.meter_mode=val
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
    saveSettings.settingsChanged=True

def handleRawFormatChange(event):
    val=str(event)
    settings["raw_format"]=val
    cam.raw_format=val
    saveSettings.settingsChanged=True
    
def handleExposureModeChange(event):
    val=str(event)
    settings["exposure_mode"]=val
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
    settings["direction"]=val
    saveSettings.settingChanged=True

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
iso=Scale(miniFrame,from_=100,to=800,resolution=100,length=scr_w/6-widget_w,width=8,orient=HORIZONTAL,command=handleIsoChange)
iso.set(settings["iso"])
iso.pack(side="right")
Label(miniFrame,text="Iso:",width=widget_wchars,anchor="e").pack(side="right")
###### AUTO-EXPOSURE COMPENSATION SCALE
compensation=Scale(miniFrame,from_= -25,to=25,resolution=1,length=scr_w/3-widget_w,width=8,orient=HORIZONTAL,command=handleCompensationChange)
compensation.set(settings["exposure_compensation"])
compensation.pack(side="right")
Label(miniFrame,text="Auto Compensate:").pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
filmFormatSelector=OptionMenu(miniFrame,filmFormat,*filmFormatsList)
filmFormatSelector.config(width=widget_wchars)
filmFormatSelector.pack(side="right")
lbl=Label(miniFrame,text="Film format:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
captureModeSelector=OptionMenu(miniFrame,captureMode,*captureModesList)
captureModeSelector.config(width=widget_wchars)
captureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Capture Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
exposureModeSelector=OptionMenu(miniFrame,exposureMode,*cam.EXPOSURE_MODES.keys(),command=handleExposureModeChange)
exposureModeSelector.config(width=widget_wchars)
exposureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Exposure Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
meterModeSelector=OptionMenu(miniFrame,meterMode,*cam.METER_MODES.keys(),command=handleMeterModeChange)
meterModeSelector.config(width=widget_wchars)
meterModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Meter Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
awbModeSelector=OptionMenu(miniFrame,awbMode,*cam.AWB_MODES.keys(),command=handleAwbModeChange)
awbModeSelector.config(width=widget_wchars)
awbModeSelector.pack(side="right")
lbl=Label(miniFrame,text="AWB Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
imageEffectSelector=OptionMenu(miniFrame,imageEffect,*cam.IMAGE_EFFECTS,command=handleImageEffectChange)
imageEffectSelector.config(width=widget_wchars)
imageEffectSelector.pack(side="right")
lbl=Label(miniFrame,text="ImageEffect:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
rawFormatSelector=OptionMenu(miniFrame,rawFormat,*cam.RAW_FORMATS,command=handleRawFormatChange)
rawFormatSelector.config(width=widget_wchars)
rawFormatSelector.pack(side="right")
lbl=Label(miniFrame,text="Raw Format:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
possibleDirections=("cw","ccw")
directionSelector=OptionMenu(miniFrame,direction,*possibleDirections,command=handleDirectionChange)
directionSelector.config(width=widget_wchars)
directionSelector.pack(side="right")
lbl=Label(miniFrame,text="Reels Direction:",width=widget_wchars,anchor="e")
lbl.pack(side="right")



miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
SaveButton=Button(miniFrame, text="Save Settings", width=widget_wchars, command=saveSettings)

SaveButton.pack(side="right")



miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
message=Label(miniFrame,text="",anchor="e")
message.pack(side="right")

handleAwbModeChange(awbMode.get())
handleExposureModeChange(exposureMode.get())

saveSettings.settingsChanged=False
def click_handler(event):
    global previewSize
    step=sqrt(2.0)
    zoomLimit=16.0
    z=click_handler.zoom
    oldfactor=1.0/(z[2]-z[0])
    #message.configure(text="{} at {},{}".format(event.num, event.x, event.y))
    if event.num == 3:
        # reset zoom
        click_handler.zoom=(0.0,0.0,1.0,1.0)
        cam.zoom=click_handler.zoom
        message.configure(text="zoom factor: 1.00")
    if event.num == 4:
        # ZOOM IN
        if oldfactor >= zoomLimit:
            return
        factor=step*oldfactor
        if factor > zoomLimit:
            factor=zoomLimit
        maxXY=1.0-(1/factor)
        posX=float(event.x)/float(previewSize[0])
        newX=z[0]+posX/oldfactor-(0.5/factor)
        if newX < 0.0:
            newX = 0.0
        if newX > maxXY:
            newX=maxXY
        posY=float(event.y)/float(previewSize[1])
        newY=z[1]+posY/oldfactor-(0.5/factor)
        if newY < 0.0:
            newY = 0.0
        if newY > maxXY:
            newY=maxXY
        z=(newX,newY,newX+(1.0/factor),newY+(1.0/factor))
        cam.zoom=z
        click_handler.zoom=z
        message.configure(text="zoom factor: {:.2f}".format(factor))
    elif event.num == 5:
        # ZOOM OUT
        if oldfactor < 0.0000001:
            return
        factor=oldfactor/step
        if factor < 1.0:
            factor=1.0
        maxXY=1.0-(1/factor)
        posX=float(event.x)/float(previewSize[0])
        newX=z[0]+posX/oldfactor-(0.5/factor)
        if newX < 0.0:
            newX = 0.0
        if newX > maxXY:
            newX=maxXY
        posY=float(event.y)/float(previewSize[1])
        newY=z[1]+posY/oldfactor-(0.5/factor)
        if newY < 0.0:
            newY = 0.0
        if newY > maxXY:
            newY=maxXY
        z=(newX,newY,newX+(1.0/factor),newY+(1.0/factor))
        cam.zoom=z
        click_handler.zoom=z
        message.configure(text="zoom factor: {:.2f}".format(factor))
        
            
click_handler.zoom=(0.0,0.0,1.0,1.0)    
    
picFrame.bind("<Button>",click_handler)


root.mainloop()

