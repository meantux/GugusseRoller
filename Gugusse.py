#!/usr/bin/python
################################################################################
# Gugusse.py
# 
#
# By: Denis-Carl Robidoux
# Gugusse Roller main file.
#
################################################################################
from AcceleratedMotor import AcceleratedMotor
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
      self.motor.Move()


class Gugusse():
    def __init__(self, cfg, start_frame):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=AcceleratedMotor(cfg["filmdrive"])
        self.feeder=AcceleratedMotor(cfg["feeder"])
        self.pickup=AcceleratedMotor(cfg["pickup"])
        self.enablePin=cfg["motorEnablePin"]
        self.cam=PiCamera()
        self.cam.resolution=self.cam.MAX_RESOLUTION
        self.cam.awb_mode='off'
        self.cam.awb_gains=(Fraction(229,256),Fraction(763,256))
        self.cam.shutter_speed=16660
        self.cam.start_preview(resolution=(1440,1080))
        self.framecount=start_frame
        try:
            os.mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares");
        GPIO.setup(self.enablePin, GPIO.OUT, initial=1)
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive,1000 )
        m2=MotorThread(self.feeder,1000)
        m3=MotorThread(self.pickup,1000)
        m1.start()
        m3.start()
        # by limiting only 2 motors running at a time
        # we're lowering the maximum electrical consumption
        m3.join()
        m2.start()
        m2.join()
        m1.join()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           GPIO.output(self.enablePin, 0)
           raise Exception("Motor Fault!")
        fn="/dev/shm/%05d.jpg"%self.framecount
        fncomplete="/dev/shm/complete/%05d.jpg"%self.framecount
        print("exposure_speed={}".format(self.cam.exposure_speed))
        self.framecount+= 1
        try:
           self.cam.capture(fn)
        except exception as e:
           GPIO.output(self.enablePin, 0)
           print("Failure to capture image: {}".format(e))
           raise Exception("Stop")
        os.rename(fn,fncomplete)
        

        
import sys
try:
   h=open(sys.argv[1])
   filmcfg=json.load(h)
   h.close()
   h=open("hardwarecfg.json")
   cfg=json.load(h)
   for device in filmcfg:
      cfg[device].update(filmcfg[device])
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
