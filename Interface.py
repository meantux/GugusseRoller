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

awbMode=StringVar(root)
awbMode.set(settings["awb_mode"])

imageEffect=StringVar(root)
imageEffect.set(settings["image_effect"])

def handleExposureChange(event):
    settings["shutter_speed"]=int(event)
    cam.shutter_speed=int(event)

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
    cam.awb_mode=val
    if val == "off":
        wbGain1.configure(state="normal")
        wbGain2.configure(state="normal")
    else:
        wbGain1.configure(state="disabled")
        wbGain2.configure(state="disabled")
    

def handleExposureModeChange(event):
    val=str(event)
    settings["exposure_mode"]=val
    if val == "off":
        exposition.configure(state="normal",fg="black")    
    else:
        exposition.configure(state="disabled",fg="gray")
    cam.exposure_mode=val
        

miniFrame=Frame(topFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
exposition=Scale(miniFrame,from_=1,to=32767,length=scr_w-widget_w,width=8,orient=HORIZONTAL,command=handleExposureChange)
exposition.set(settings["shutter_speed"])
exposition.pack(side="right")
miniFrame=Frame(miniFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="right",ipadx=widget_w)
Label(miniFrame,text="Exposure:").pack(side="right")

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
exposureModeSelector=OptionMenu(miniFrame,exposureMode,*cam.gcCamModes,command=handleExposureModeChange)
exposureModeSelector.config(width=widget_wchars)
exposureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Exposure Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top",fill="x")
awbModeSelector=OptionMenu(miniFrame,awbMode,*cam.gcAwbModes,command=handleAwbModeChange)
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

if str(awbModeSelector) != "off":
    wbGain1.configure(state="disabled")
    wbGain2.configure(state="disabled")

if exposureMode.get() != "off":
    print("mode is {}".format(exposureMode.get()))
    exposition.configure(state="disabled")





root.mainloop()
