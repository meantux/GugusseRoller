#!/usr/bin/python3
################################################################################
# Gugusse.py
# 
#
# By: Denis-Carl Robidoux
# Gugusse Roller main file.
#
################################################################################
from TrinamicSilentMotor import TrinamicSilentMotor
from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from ICamera import ICamera
from fractions import Fraction
from Lights import Lights
import os
GPIO.setmode(GPIO.BCM) 

class MotorThread (threading.Thread):
   def __init__(self, motor):
      threading.Thread.__init__(self)
      self.motor=motor
   def run(self):
      self.motor.move()


class Gugusse():
    def __init__(self, cfg, start_frame):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=TrinamicSilentMotor(cfg["filmdrive"], trace=True)
        self.feeder=TrinamicSilentMotor(cfg["feeder"],autoSpeed=True)
        self.pickup=TrinamicSilentMotor(cfg["pickup"],autoSpeed=True)
        try:
            os.mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares?");
        self.feeder.enable()
        self.filmdrive.enable()
        self.pickup.enable()
        self.cam=ICamera(start_frame)
        self.lights=Lights("on")
        
           
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive)
        m2=MotorThread(self.feeder)
        m3=MotorThread(self.pickup)
        #self.cam.gcApplySettings()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           self.lights.set("off")
           raise Exception("Motor Fault!")
        sleep(1)
        try:
           self.cam.captureCycle()
        except Exception as e:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           print("Failure to capture image: {}".format(e))
           self.cam.close()
           self.lights.set("off")
           raise Exception("Stop")
        m2.start()
        m3.start()
        m3.join()
        m2.join()
        m1.start()
        m1.join()
           

        
import sys
try:
   print("Loading film config")
   h=open(sys.argv[1])
   filmcfg=json.load(h)
   h.close()
   print("Loading hardware config")
   h=open("hardwarecfg.json")
   cfg=json.load(h)
   print("merging the 2")
   for device in filmcfg:
      print("merging {}".format(device))
      cfg[device].update(filmcfg[device])
   print("Reading the other 2 parameters")
   firstNum=int(sys.argv[2])
   feederDirection=sys.argv[3]
except Exception as e:
   print (e.message)
   print ("\nUSAGE: {} <film format json file> <initial file number> <cw|ccw>\n".format(sys.argv[0]))
   sys.exit(0)
if feederDirection == "cw":
   cfg["feeder"]["invert"]=not cfg["feeder"]["invert"]
   cfg["pickup"]["invert"]=not cfg["pickup"]["invert"]
capture=Gugusse(cfg, firstNum)
while True:
    capture.frameAdvance()
