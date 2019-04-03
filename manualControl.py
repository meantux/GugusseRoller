#!/usr/bin/python2.7
 
# adapted from https://github.com/recantha/EduKit3-RC-Keyboard/blob/master/rc_keyboard.py

from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from picamera import PiCamera
from fractions import Fraction
from PIL import Image
import os
import tty
import termios
import sys

GPIO.setmode(GPIO.BCM)
c=PiCamera()

#c.resolution=(1024,768)
#c.resolution=(1440,1080)
c.awb_mode='off'
c.awb_gains=(1.26,2.3)
c.iso=100
c.resolution=c.MAX_RESOLUTION
c.start_preview(resolution=(1440,1080))
sleep(1)
c.exposure_mode="night"
c.iso=60
c.shutter_speed=6000

img=Image.open('gfx/quadrillage.png')
pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
        ))
    # Paste the original image into the padded one
    pad.paste(img, (0, 0))


o=c.add_overlay(pad.tostring(), size=img.size)
o.alpha=128
o.layer=3

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

print("-------------")
print("FEEDER")
print("q: adv")
print("w: toggle dir")
print("e: toggle pwr")
print("-------------")
print("MAINDRIVE")
print("a: adv")
print("s: toggle dir")
print("d: toggle pwr")
print("-------------")
print("FEEDER")
print("z: adv")
print("x: toggle dir")
print("c: toggle pwr")
print("-------------")
print("ESC: exit")




while True:
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
    elif (char == "\033"):
        sys.exit(0)
