#!/usr/bin/python2.7
 
# adapted from https://github.com/recantha/EduKit3-RC-Keyboard/blob/master/rc_keyboard.py

from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from picamera import PiCamera
from fractions import Fraction
import os
import tty
import termios
import sys

GPIO.setmode(GPIO.BCM)
 
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
        self.actualToggle=GPIO.LOW

    def changeDirection(self):
        if self.actualDir==GPIO.HIGH:
            self.actualDir=GPIO.LOW
        else:
            self.actualDir=GPIO.HIGH
        print("Switching direction of {} to {}".format(self.name, self.actualDir))
        GPIO.output(self.direction, self.actualDir)

    def toggle(self):
        if self.actualToggle==GPIO.LOW:
            self.actualToggle=GPIO.HIGH
        else:
            self.actualToggle=GPIO.LOW
        GPIO.output(self.enable, self.actualToggle)
        
    def move (self,count,delay=0.0005):
        print("moving {} {} clicks with a delay of {} between each".format(self.name, count, delay))
        while count>0:
            if self.toggle==GPIO.LOW:
                self.toggle=GPIO.HIGH
            else:
                self.toggle=GPIO.LOW
            GPIO.output(self.step, self.toggle)
            sleep(delay)
            count-= 1

filmdrive=SimpleMotor("filmdrive")
feeder=SimpleMotor("feeder")
pickup=SimpleMotor("pickup")

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
