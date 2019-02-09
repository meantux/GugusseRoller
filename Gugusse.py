#!/usr/bin/python
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
from picamera import PiCamera
from fractions import Fraction
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
        self.feeder=TrinamicSilentMotor(cfg["feeder"])
        self.pickup=TrinamicSilentMotor(cfg["pickup"])
        self.cam=PiCamera()
        self.cam.resolution=self.cam.MAX_RESOLUTION
        #self.cam.awb_mode='off'
        #self.cam.awb_gains=(Fraction(229,256),Fraction(763,256))
        #self.cam.shutter_speed=16660*4
        self.cam.start_preview(resolution=(1440,1080))
        self.framecount=start_frame
        try:
            os.mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares");
        self.feeder.enable()
        self.filmdrive.enable()
        self.pickup.enable()
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive)
        m2=MotorThread(self.feeder)
        m3=MotorThread(self.pickup)
        m1.start()
        m3.start()
        # by limiting only 2 motors running at a time
        # we're lowering the maximum electrical consumption
        m3.join()
        m2.start()
        m2.join()
        m1.join()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           raise Exception("Motor Fault!")
        fn="/dev/shm/%05d.jpg"%self.framecount
        fncomplete="/dev/shm/complete/%05d.jpg"%self.framecount
        #print("exposure_speed={}".format(self.cam.exposure_speed))
        self.framecount+= 1
        try:
           self.cam.capture(fn)
        except exception as e:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           print("Failure to capture image: {}".format(e))
           raise Exception("Stop")
        os.rename(fn,fncomplete)
        

        
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
capture=Gugusse(cfg, firstNum)
while True:
    capture.frameAdvance()
    sleep(0.1)
