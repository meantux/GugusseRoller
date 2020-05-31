#!/usr/bin/python3
 
# adapted from https://github.com/recantha/EduKit3-RC-Keyboard/blob/master/rc_keyboard.py

from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from GCamera import GCamera
from fractions import Fraction
from PIL import Image
import os
import tty
import termios
from threading import Thread
import sys

GPIO.setmode(GPIO.BCM)

h=open("cameraSettings.json", "r")
camsettings=json.load(h)
h.close()

c=GCamera()


img=Image.open('gfx/quadrillage.png')
pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
        ))
# Paste the original image into the padded one
pad.paste(img, (0, 0))


o=c.add_overlay(pad.tobytes(), size=img.size, window=(256,0,1024,768))
o.fullscreen=False
o.window=(256,0,1024,768)
o.alpha=0
o.layer=3


loopInputs=True

def displayInputs(pinA, pinB, pinC):
    GPIO.setup(pinA, GPIO.IN)
    GPIO.setup(pinB, GPIO.IN)
    GPIO.setup(pinC, GPIO.IN)
    sleep (2)
    while loopInputs:
        print("\033[0;0H\n                                           \n\rINPUTS:{}|{}|{}                                \n".format(GPIO.input(pinA),GPIO.input(pinB),GPIO.input(pinC)))
        sleep(0.05)
    


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

class SimpleMotor:
    def __init__(self, name):
        self.name=name
        print("Loading hardware config")
        h=open("hardwarecfg.json")
        cfg=json.load(h)
        h.close()
        self.enable=cfg[name]["pinEnable"]
        self.direction=cfg[name]["pinDirection"]
        self.step=cfg[name]["pinStep"]
        self.invert=cfg[name]["invert"]
        GPIO.setup(self.enable, GPIO.OUT, initial=GPIO.LOW)
        if self.invert:
            self.actualDir=GPIO.LOW
        else:
            self.actualDir=GPIO.HIGH
        GPIO.setup(self.direction, GPIO.OUT, initial=self.actualDir)
        GPIO.setup(self.step, GPIO.OUT, initial=GPIO.LOW)
        self.actualState=GPIO.LOW
        self.actualToggle=GPIO.LOW
        self.stopPin=cfg[name]["stopPin"]
    def changeDirection(self):
        if self.actualDir==GPIO.HIGH:
            self.actualDir=GPIO.LOW
        else:
            self.actualDir=GPIO.HIGH
        #print("Switching direction of {} to {}".format(self.name, self.actualDir))
        GPIO.output(self.direction, self.actualDir)

    def toggle(self):
        if self.actualToggle==GPIO.LOW:
            self.actualToggle=GPIO.HIGH
        else:
            self.actualToggle=GPIO.LOW
        GPIO.output(self.enable, self.actualToggle)
        
    def move (self,count,delay=0.0005):
        #print("moving {} {} clicks with a delay of {} between each".format(self.name, count, delay))
        while count>0:
            if self.actualState==GPIO.LOW:
                self.actualState=GPIO.HIGH
            else:
                self.actualState=GPIO.LOW
            GPIO.output(self.step, self.actualState)
            sleep(delay)
            count-= 1

filmdrive=SimpleMotor("filmdrive")
feeder=SimpleMotor("feeder")
pickup=SimpleMotor("pickup")
t=Thread(target=displayInputs, args=(feeder.stopPin,filmdrive.stopPin,pickup.stopPin))
t.start()
sleep(0.1)
for line in range(0,60):
    print("                             ")
print("-------------")
print("FEEDER")
print("q: adv, w: dir")
print("e: toggle pwr")
print("-------------")
print("MAINDRIVE")
print("a: adv, s: dir")
print("d: toggle pwr")
print("-------------")
print("FEEDER")
print("z: adv, x: dir")
print("c: toggle pwr")
print("-------------")
print("1 to 9: zooms")
print("0: reset zoom")
print("p: inc compensation")
print("o: dec compensation")
print("f: freeze WB")
print("g: next WB mode")
print("rtyu: manual WB adj")
print("h: next EXP mode")
print("j: Enter Exposure")
print("v b: contrast")
print("n m: brightness")
print("k: change capture mode")
print("ESC: exit")
print("SPC: toggle grid")

overlay=False
def toggleOverlay(o, overlay):
    if overlay:
        o.alpha=0
    else:
        o.alpha=196
    return not overlay
    
while True:
    for line in range(5,20):
        print("\033[{};0H                                            \n".format(line))
    print("\033[5;0H{}".format(json.dumps(c.gcSettings, indent=2)))
    print(c.captureModes[c.gcSettings["captureMode"]]["description"])
    char = getch()
    if (char == "q"):
        feeder.move(1000)
    elif (char == "w"):
        feeder.changeDirection()
    elif (char == "e"):
        feeder.toggle()
    elif (char == "a"):
        filmdrive.move(1000)        
    elif (char == "s"):
        filmdrive.changeDirection()
    elif (char == "d"):
        filmdrive.toggle()
    elif (char == "z"):        
        pickup.move(1000)
    elif (char == "x"):
        pickup.changeDirection()
    elif (char == "c"):
        pickup.toggle()
    elif (char == "p"):
        c.gcSettings["exposure_compensation"]+=1
        try:
            c.exposure_compensation=c.gcSettings["exposure_compensation"]
        except Exception:
            c.gcSettings["exposure_compensation"]-=1
        c.gcSaveSettings()
    elif (char == "o"):
        c.gcSettings["exposure_compensation"]-= 1
        try:
            c.exposure_compensation=c.gcSettings["exposure_compensation"]
        except Exception:
            c.gcSettings["exposure_compensation"]+= 1
        c.gcSaveSettings()
    elif (char == " "):
        overlay=toggleOverlay(o,overlay)
    elif char in [ "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]:
        c.zoom=c.gcZooms[int(char)]
    elif char == "f":
        c.freezeWhiteBalance()
    elif char in ["r","t","y","u"]:
        if char=="r":
            c.gcSettings["awb_gains"][0]=c.gcSettings["awb_gains"][0]/1.05
        elif char=="t":
            c.gcSettings["awb_gains"][0]=c.gcSettings["awb_gains"][0]*1.05            
        elif char=="y":
            c.gcSettings["awb_gains"][1]=c.gcSettings["awb_gains"][1]/1.05
            
        elif char=="u":
            c.gcSettings["awb_gains"][1]=c.gcSettings["awb_gains"][1]*1.05
        c.gcSaveSettings()
        c.awb_gains=c.gcSettings["awb_gains"]
            
    elif char == "g":
        c.awb_mode=c.selectOther(c.awb_mode, c.gcAwbModes, 1)
        c.gcSettings["awb_mode"]=c.awb_mode
        c.gcSaveSettings()
    elif char == "h":
        c.exposure_mode=c.selectOther(c.exposure_mode, c.gcCamModes, 1)
        c.gcSettings["exposure_mode"]=c.exposure_mode
        c.gcSaveSettings()
    elif char == "j":
        val= -1
        try:
            val=int(raw_input("Enter value: "))
        except Exception:
            pass        
        if val >= 0:
            c.shutter_speed=val
        print("exposure: {}".format(c.shutter_speed))
        c.gcSettings["shutter_speed"]=val
        c.gcSaveSettings()
    elif (char == "v"):
        c.gcSettings["contrast"]-= 1
        try:
            c.contrast=c.gcSettings["contrast"]
        except Exception:
            c.gcSettings["contrast"]+= 1
        c.gcSaveSettings()
    elif (char == "b"):
        c.gcSettings["contrast"]+= 1
        try:
            c.contrast=c.gcSettings["contrast"]
        except Exception:
            c.gcSettings["contrast"]-= 1
        c.gcSaveSettings()
    elif (char == "n"):
        c.gcSettings["brightness"]-= 1
        try:
            c.brightness=c.gcSettings["brightness"]            
        except Exception:
            c.gcSettings["brightness"]+= 1
        c.gcSaveSettings()
    elif (char == "m"):
        c.gcSettings["brightness"]+= 1
        try:
            c.brightness=c.gcSettings["brightness"]
        except Exception:
            c.gcSettings["brightness"]-= 1
        c.gcSaveSettings()            
    elif char == "k":
        c.gcSettings["captureMode"]=c.captureModes[c.gcSettings["captureMode"]]["next"]
        c.gcSaveSettings()
    elif (char == "\033"):
        break

loopInputs=False
sleep(0.2)
t.join()
c.close()
print("\033[0J")
