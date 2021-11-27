#!/usr/bin/python3

from tkinter import *
from tkinter import messagebox
from json import load,dump
from copy import deepcopy
from ftplib import FTP
from datetime import datetime
from os import remove
from TrinamicSilentMotor import TrinamicSilentMotor

root=Tk()

root.winfo_toplevel().title("Gugusse Roller Configure")

with open("hardwarecfg.json","rt") as h:
    hardware=load(h)

with open("ftp.json","rt") as h:
    ftp=load(h)

server=StringVar(root)
server.set(ftp["server"])
user=StringVar(root)
user.set(ftp["user"])
passwd=StringVar(root)
passwd.set(ftp["passwd"])
path=StringVar(root)
path.set(ftp["path"])

feeder=BooleanVar(root)
feeder.set(hardware["feeder"]["invert"])

filmdrive=BooleanVar(root)
filmdrive.set(hardware["filmdrive"]["invert"])

pickup=BooleanVar(root)
pickup.set(hardware["pickup"]["invert"])

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
Button(miniFrame,text="Test FTP settings",command=testFTP).pack(side="left")


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
    with open("ftp.json","wt") as h:
        dump(ftp, h, sort_keys=True, indent=4)
    hardware["feeder"]["invert"]=feeder.get()
    hardware["filmdrive"]["invert"]=filmdrive.get()
    hardware["pickup"]["invert"]=pickup.get()
    with open("hardwarecfg.json","wt") as h:
        dump(hardware, h, sort_keys=True, indent=4)
    root.destroy()

miniFrame=Frame(root, highlightbackground="black", highlightthickness=1)
miniFrame.pack(side="top", fill="x")
Button(miniFrame,text="Save And Exit",command=saveExit).pack(side="right")
Button(miniFrame,text="Cancel",command=root.destroy).pack(side="left")

root.mainloop()

