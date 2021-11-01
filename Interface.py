#!/usr/bin/python3
from tkinter import *
from json import load

root= Tk()
scr_w = root.winfo_screenwidth()
scr_h = root.winfo_screenheight()
widget_h=4
widget_w=120
widget_wchars=16
top_h=10*widget_h
left_w=2*widget_w



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

captureMode=StringVar(root)
captureMode.set(settings["captureMode"])

miniFrame=Frame(leftFrame,bg="blue")
miniFrame.pack(side="top",fill="x")
captureModeSelector=OptionMenu(miniFrame,captureMode,*captureModesList)
captureModeSelector.config(width=widget_wchars)
captureModeSelector.pack(side="right")
lbl=Label(miniFrame,text="Capture Mode:")
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
wbGain1=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
wbGain1.set(settings["awb_gains"][0])
wbGain1.pack(side="right")
subMiniFrame=Frame(miniFrame,bg="magenta")
subMiniFrame.pack(side="right",fill="both")
subMiniFrame.config(width=widget_w)
Label(subMiniFrame,text="WB Gain 1:").pack(side="right")
              
wbGain2=Scale(miniFrame,from_=0.1,to=7.95,length=int(scr_w/2-widget_w),width=8,resolution=0.005,orient=HORIZONTAL)
wbGain2.set(settings["awb_gains"][1])
wbGain2.pack(side="right")
Label(miniFrame,text="WB Gain 2:").pack(side="right")
              


root.mainloop()
