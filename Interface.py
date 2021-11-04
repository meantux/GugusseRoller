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

topFrame=Frame(root,bg="red")
topFrame.pack(side="top",fill="both")
leftFrame=Frame(root,bg="green")
leftFrame.pack(side="left",fill="both")
Label(topFrame,text="Gugusse Roller",bg="red").pack(side="top")

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

imageEffect=StringVar(root)
imageEffect.set(settings["image_effect"])



miniFrame=Frame(leftFrame,bg="white")
miniFrame.pack(side="top",fill="x")
filmFormatSelector=OptionMenu(miniFrame,filmFormat,*filmFormatsList)
filmFormatSelector.config(width=widget_wchars)
filmFormatSelector.pack(side="right")
lbl=Label(miniFrame,text="Film format:",width=widget_wchars,anchor="e")
lbl.pack(side="right")


miniFrame=Frame(leftFrame,bg="blue")
miniFrame.pack(side="top",fill="x")
captureModeSelector=OptionMenu(miniFrame,captureMode,*captureModesList)
captureModeSelector.config(width=widget_wchars)
captureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Capture Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame,bg="white")
miniFrame.pack(side="top",fill="x")
exposureModeSelector=OptionMenu(miniFrame,exposureMode,*cam.gcCamModes)
exposureModeSelector.config(width=widget_wchars)
exposureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Exposure Mode:",width=widget_wchars,anchor="e")
lbl.pack(side="right")

miniFrame=Frame(leftFrame,bg="red")
miniFrame.pack(side="top",fill="x")
imageEffectSelector=OptionMenu(miniFrame,imageEffect,*cam.IMAGE_EFFECTS)
imageEffectSelector.config(width=widget_wchars)
imageEffectSelector.pack(side="right")
lbl=Label(miniFrame,text="ImageEffect:",width=widget_wchars,anchor="e")
lbl.pack(side="right")





miniFrame=Frame(topFrame,bg="purple")
miniFrame.pack(side="top",fill="x")
exposition=Scale(miniFrame,from_=1,to=32767,length=scr_w-widget_w,width=8,orient=HORIZONTAL)
exposition.set(settings["shutter_speed"])
exposition.pack(side="right")
miniFrame=Frame(miniFrame,bg="cyan")
miniFrame.pack(side="right",ipadx=widget_w)
Label(miniFrame,text="Exposure:").pack(side="right")

miniFrame=Frame(topFrame,bg="yellow")
miniFrame.pack(side="top",fill="x")
wbGain2=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
wbGain2.set(settings["awb_gains"][1])
wbGain2.pack(side="right")
Label(miniFrame,text="      WB Gain 2:",width=widget_wchars,anchor="e").pack(side="right")
              
wbGain1=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
wbGain1.set(settings["awb_gains"][0])
wbGain1.pack(side="right")
Label(miniFrame,text="WB Gain 1:").pack(side="right")

miniFrame=Frame(topFrame,bg="orange")
miniFrame.pack(side="top",fill="x")
contrast=Scale(miniFrame,from_= -100,to=100,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
contrast.set(settings["contrast"])
contrast.pack(side="right")
Label(miniFrame,text="Contrast:",width=widget_wchars,anchor="e").pack(side="right")
              
wbGain1=Scale(miniFrame,from_=0,to=100,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
wbGain1.set(settings["brightness"])
wbGain1.pack(side="right")
Label(miniFrame,text="Brightness:").pack(side="right")
              

root.mainloop()
