#!/usr/bin/python3
from tkinter import *
from json import load
from GCamera import GCamera

root= Tk()
scr_w = root.winfo_screenwidth()
scr_h = root.winfo_screenheight()
widget_h=4
widget_wchars=14
widget_w=widget_wchars*10
top_h=140
left_w=2*widget_w

cam=GCamera()
px=2*widget_w
py=top_h
pw=scr_w-px
ph=scr_h-py
cam.start_preview(fullscreen=False,resolution=(1440,1080),window=(px,py,pw,ph),vflip=False,hflip=False)
root.attributes("-fullscreen",True)

topFrame=Frame(root, highlightbackground="black", highlightthickness=1)
topFrame.pack(side="top",fill="both")
leftFrame=Frame(root, highlightbackground="black", highlightthickness=1)
leftFrame.pack(side="left",fill="both")
topLabel=Label(topFrame,text="Gugusse Roller")
topLabel.pack(side="top")

with open("cameraSettings.json","rt") as h:
    settings=load(h)
    h.close()

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

def handleExposureChange(event):
    settings["shutter_speed"]=int(event)
    cam.shutter_speed=int(event)

def handleMeterModeChange(event):
    val=str(event)
    settings["meter_mode"]=val
    cam.meter_mode=val

def handleWbGain1(event):
    settings["awb_gains"][0]=float(event)
    cam.awb_gains=settings["awb_gains"]

def handleWbGain2(event):
    settings["awb_gains"][1]=float(event)
    cam.awb_gains=settings["awb_gains"]

def  handleImageEffectChange(event):
    val=str(event)
    settings["image_effect"]=val
    cam.image_effect=val

def handleAwbModeChange(event):
    val=str(event)
    settings["awb_mode"]=val
    #if val == "off":
    #    wbGain1.configure(state="normal")
    #    wbGain2.configure(state="normal")
    #        
    #    
    #else:
    #    wbGain1.configure(state="disabled")
    #    wbGain2.configure(state="disabled")
    cam.awb_mode=val

def handleRawFormatChange(event):
    val=str(event)
    settings["raw_format"]=val
    cam.raw_format=val
    

def handleExposureModeChange(event):
    val=str(event)
    settings["exposure_mode"]=val
    if val == "off":
        exposition.configure(state="normal",fg="black")    
        if handleExposureModeChange.ExposureWasNotOff:
            exposition.set(20000)
            cam.shutter_speed=20000
            #handleExposureModeChange.ExposureWasNotOff=False
    #else:
        #exposition.configure(state="disabled",fg="gray")
        #handleExposureModeChange.ExposureWasNotOff=True
    cam.exposure_mode=val

def handleIsoChange(event):
    val=int(event)
    settings["iso"]=val
    cam.iso=val
    analog_gain.configure(text="Gain: {}".format(float(cam.analog_gain)))

handleExposureModeChange.ExposureWasNotOff=False



miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
imageEffect=StringVar(root)
imageEffect.set(settings["image_effect"])


miniFrame.pack(side="top",fill="x")
exposition=Scale(miniFrame,from_=1,to=32700,resolution=100,length=scr_w/2-widget_w,width=8,orient=HORIZONTAL,command=handleExposureChange)
exposition.set(settings["shutter_speed"])
exposition.pack(side="right")
Label(miniFrame,text="Exposure:",width=widget_wchars,anchor="e").pack(side="right")

iso=Scale(miniFrame,from_=100,to=800,resolution=100,length=scr_w/2-widget_w,width=8,orient=HORIZONTAL,command=handleIsoChange)
iso.set(settings["iso"])
iso.pack(side="right")
Label(miniFrame,text="Iso:").pack(side="right")


miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
wbGain2=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL,command=handleWbGain2)
wbGain2.set(settings["awb_gains"][1])
wbGain2.pack(side="right")
Label(miniFrame,text="      WB Gain 2:",width=widget_wchars,anchor="e").pack(side="right")
              
wbGain1=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL,command=handleWbGain1)
wbGain1.set(settings["awb_gains"][0])
wbGain1.pack(side="right")
Label(miniFrame,text="WB Gain 1:").pack(side="right")

miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
contrast=Scale(miniFrame,from_= -100,to=100,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
contrast.set(settings["contrast"])
contrast.pack(side="right")
Label(miniFrame,text="Contrast:",width=widget_wchars,anchor="e").pack(side="right")
              
brightness=Scale(miniFrame,from_=0,to=100,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
brightness.set(settings["brightness"])
brightness.pack(side="right")
Label(miniFrame,text="Brightness:").pack(side="right")

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
analog_gain=Label(miniFrame,text="analog_gain=?",width=widget_wchars,anchor="e")
analog_gain.pack(side="right")

#if str(awbModeSelector) != "off":
#    wbGain1.configure(state="disabled")
#    wbGain2.configure(state="disabled")

#if exposureMode.get() != "off":
#    print("mode is {}".format(exposureMode.get()))
#    exposition.configure(state="disabled")
              

root.mainloop()
