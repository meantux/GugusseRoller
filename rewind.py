#!/usr/bin/python
################################################################################
# rewind.py
# 
#
# By: Denis-Carl Robidoux
# To rewind the film after the capture.
#
################################################################################
from AcceleratedMotor import AcceleratedMotor
from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
GPIO.setmode(GPIO.BCM) 

class MotorThread (threading.Thread):
   def __init__(self, motor, maxClicks):
      threading.Thread.__init__(self)
      self.motor=motor
      self.maxClicks=maxClicks
   def run(self):
      self.motor.setMove(self.maxClicks)


class Rewind():
    def __init__(self, cfg):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        # We rewinding so...
        cfg["feeder"]["invert"] = not cfg["feeder"]["invert"]
        cfg["feeder"]["accel"]=10
        cfg["feeder"]["ignoreInitial"]=0
        cfg["feeder"]["speed"]=1200
        self.feeder=AcceleratedMotor(cfg["feeder"])
        #self.pickup=AcceleratedMotor(cfg["pickup"])
        # Enable all H-Bridges chips
        self.enablePin=cfg["motorEnablePin"]
        GPIO.setup(self.enablePin, GPIO.OUT, initial=1)
        # Now that all motors are enabled we still need
        # to disable the pickup reel so we set all its pins
        # to the same value (that's one way to disable
        # a motor driven by H-Bridges).
        for pin in cfg["pickup"]["pins"]:
           GPIO.setup(pin, GPIO.OUT, initial=0)
       
    def frameAdvance(self):
        m2=MotorThread(self.feeder,100000000)
        m2.start()
        m2.join()
        
import sys
try:
   h=open("hardwarecfg.json")
   cfg=json.load(h)
except Exception as e:
   print (e.message)
   print ("\nUSAGE: {} <motor json file>\n".format(sys.argv[0]))
   sys.exit(0)

reelback=Rewind(cfg)
print ("Remember to manually unaligned the left arm from its optical sensor")
print ("When you're done rewinding, just re-align the left arm to exit")
reelback.frameAdvance()
