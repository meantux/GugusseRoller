#!/usr/bin/python3

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from json import load,dump
from copy import deepcopy
from ftplib import FTP
from datetime import datetime
from os import remove
from TrinamicSilentMotor import TrinamicSilentMotor
from ConfigFiles import ConfigFiles


root=Tk()

root.winfo_toplevel().title("Gugusse Roller Configure")

hardware=ConfigFiles("hardwarecfg.json")
ftp=ConfigFiles("ftp.json")

if "saveMode" not in hardware:
    hardware["saveMode"]="ftp"
    hardware["localFilePath"]="/media"
    
server=StringVar(root)
server.set(ftp["server"])
user=StringVar(root)
user.set(ftp["user"])
passwd=StringVar(root)
passwd.set(ftp["passwd"])
path=StringVar(root)
path.set(ftp["path"])
localFilePath=StringVar(root)
localFilePath.set(hardware["localFilePath"])

feeder=BooleanVar(root)
feeder.set(hardware["feeder"]["invert"])

filmdrive=BooleanVar(root)
filmdrive.set(hardware["filmdrive"]["invert"])

pickup=BooleanVar(root)
pickup.set(hardware["pickup"]["invert"])

saveMode=StringVar(root)
saveMode.set(hardware["saveMode"])

def modeChangeHandler(event):
    val=str(event)
    hardware["saveMode"]=val
    if val == "ftp":
        serverBox.configure(state="normal",fg="black")
        userBox.configure(state="normal",fg="black")
        passwdBox.configure(state="normal",fg="black")
        pathBox.configure(state="normal",fg="black")
        testButton.configure(state="normal",fg="black")
        filePathButton.configure(state="disabled",fg="grey")
    elif val == "local":
        serverBox.configure(state="disabled",fg="grey")
        userBox.configure(state="disabled",fg="grey")
        passwdBox.configure(state="disabled",fg="grey")
        pathBox.configure(state="disabled",fg="grey")
        testButton.configure(state="disabled",fg="grey")
        filePathButton.configure(state="normal",fg="black")
        
def getTheFileDialog():
    oldLocalPath=hardware["localFilePath"]
    newLocalPath=str(filedialog.askdirectory(initialdir=oldLocalPath,mustexist=True))
    print("We got \"{}\"".format(newLocalPath))
    # why sometimes we click Cancel in askdirectory,
    # it returns "" and other times "()" eludes me...
    if newLocalPath!="" and newLocalPath!="()":
        hardware["localFilePath"]=newLocalPath
        filePathButton.configure(text=newLocalPath)


miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
saveModeSelect=OptionMenu(miniFrame,saveMode,"ftp","local",command=modeChangeHandler)
saveModeSelect.pack(side="right")
Label(miniFrame,text="Export Mode:",anchor="e").pack(side="right")

                      
miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
serverBox=Entry(miniFrame,textvariable=server)
serverBox.pack(side="right")
Label(miniFrame,text="ftp server address:",anchor="e").pack(side="right")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
userBox=Entry(miniFrame,textvariable=user)
userBox.pack(side="right")
Label(miniFrame,text="username:",anchor="e").pack(side="right")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
passwdBox=Entry(miniFrame,textvariable=passwd)
passwdBox.pack(side="right")
Label(miniFrame,text="password:",anchor="e").pack(side="right")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
pathBox=Entry(miniFrame,textvariable=path)
pathBox.pack(side="right")
Label(miniFrame,text="ftp path:",anchor="e").pack(side="right")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
filePathButton=Button(miniFrame,text=hardware["localFilePath"], command=getTheFileDialog)
filePathButton.pack(side="left")

def testFTP():
    name=datetime.now().strftime("%Y%m%d%H%M%S%f")
    try:
        conn=FTP(server.get())
        conn.login(user=user.get(),passwd=passwd.get())
        if path.get() != "" and path.get() != ".":            
            conn.cwd(path.get())
        conn.mkd(name)
        conn.cwd(name)
        with open("/dev/shm/0000.txt","wt")as h:
            h.write(name)
            h.close()
        with open("/dev/shm/0000.txt","rb") as h:
            conn.storbinary("STOR 0000.txt",h)
            h.close()
        remove("/dev/shm/0000.txt")
        conn.delete("0000.txt")
        conn.close()
        conn=FTP(server.get())
        conn.login(user=user.get(),passwd=passwd.get())
        if path.get() != "" and path.get() != ".":            
            conn.cwd(path.get())
        conn.rmd(name)
        conn.close()
        messagebox.showinfo("SUCCESS","It seems to work")
    except Exception as e:
        messagebox.showerror("Error",e)
        
                     

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
testButton=Button(miniFrame,text="Test FTP settings",command=testFTP)
testButton.pack(side="left")


def testFeeder():
    cfg=deepcopy(hardware["feeder"])
    cfg["invert"]=feeder.get()
    m=TrinamicSilentMotor(cfg)
    m.setDirection("cw")
    m.blindMove(2000)
    messagebox.showinfo("FEEDER PLATEAU", "The feeder plateau should have turned clockwise")
    
def testFilmdrive():
    cfg=deepcopy(hardware["filmdrive"])
    cfg["invert"]=filmdrive.get()
    m=TrinamicSilentMotor(cfg)
    m.setDirection("cw")
    m.blindMove(2000)
    messagebox.showinfo("THE SKATEBOARD WHEEL", "The skateboard wheel should have turned counter-clockwise")

def testPickup():
    cfg=deepcopy(hardware["pickup"])
    cfg["invert"]=pickup.get()
    m=TrinamicSilentMotor(cfg)
    m.setDirection("cw")
    m.blindMove(2000)
    messagebox.showinfo("PICKUP PLATEAU", "The pickup plateau should have turned clockwise")


miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
Button(miniFrame, text="Test Motor",command=testFeeder).pack(side="left")
feederCheck=Checkbutton(miniFrame, variable=feeder,text="feeder invert")
feederCheck.pack(side="left")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
Button(miniFrame, text="Test Motor",command=testFilmdrive).pack(side="left")
filmdriveCheck=Checkbutton(miniFrame, variable=filmdrive,text="main drive invert")
filmdriveCheck.pack(side="left")

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
Button(miniFrame, text="Test Motor",command=testPickup).pack(side="left")
pickupCheck=Checkbutton(miniFrame, variable=pickup,text="pickup invert")
pickupCheck.pack(side="left")


def saveExit():
    ftp["server"]=server.get()
    if " " in ftp["server"]:
        print("WARNING: SPACE CHARACTER DETECTED IN THE SERVER NAME")
    ftp["user"]=user.get()
    if " " in ftp["user"]:
        print("WARNING: SPACE CHARACTER DETECTED IN THE USER NAME")              
    ftp["passwd"]=passwd.get()
    if " " in ftp["passwd"]:
        print("WARNING: SPACE CHARACTER DETECTED IN THE PASSWORD")
    ftp["path"]=path.get()
    if " " in ftp["path"]:
        print("WARNING: SPACE CHARACTER DETECTED IN THE PATH")
    ftp.save()
    hardware["feeder"]["invert"]=feeder.get()
    hardware["filmdrive"]["invert"]=filmdrive.get()
    hardware["pickup"]["invert"]=pickup.get()
    hardware.save()
    root.destroy()

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
Button(miniFrame,text="Save And Exit",command=saveExit).pack(side="right")
Button(miniFrame,text="Cancel",command=root.destroy).pack(side="left")

modeChangeHandler(hardware["saveMode"])
root.mainloop()

