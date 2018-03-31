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
import os
GPIO.setmode(GPIO.BCM) 

class MotorThread (threading.Thread):
   def __init__(self, motor, maxClicks):
      threading.Thread.__init__(self)
      self.motor=motor
      self.maxClicks=maxClicks
   def run(self):
      self.motor.setMove(self.maxClicks)


class Gugusse():
    def __init__(self, cfg):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=AcceleratedMotor(cfg["filmdrive"])
        self.feeder=AcceleratedMotor(cfg["feeder"])
        self.pickup=AcceleratedMotor(cfg["pickup"])
        self.enablePin=cfg["motorEnablePin"]
        self.cam=PiCamera()
        self.cam.resolution=self.cam.MAX_RESOLUTION
        self.cam.start_preview(resolution=(1440,1080))
        self.framecount=0
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
        m2.start()
        # by limiting only 2 motors running at a time
        # we're lowering the maximum electrical consumption
        m2.join()
        m3.start()
        m3.join()
        m1.join()
        fn="/dev/shm/%05d.jpg"%self.framecount
        fncomplete="/dev/shm/complete/%05d.jpg"%self.framecount
        self.framecount+= 1
        self.cam.capture(fn)
        os.rename(fn,fncomplete)
        

        
import sys
try:
   h=open(sys.argv[1])
   cfg=json.load(h)
   cfg["filmFormatMaxTicks"]=int(sys.argv[2])
except Exception as e:
   print (e.message)
   print ("\nUSAGE: {} <motor json file> <number of ticks per frame for errors>\n".format(sys.argv[0]))
   sys.exit(0)
capture=Gugusse(cfg)
while True:
    capture.frameAdvance()
    sleep(0.1)
