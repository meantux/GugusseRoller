#!/usr/bin/python
################################################################################
# rewind.py
# 
#
# By: Denis-Carl Robidoux
# To rewind the film after the capture.
#
################################################################################
from TrinamicSilentMotor import TrinamicSilentMotor
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
      self.motor.move()


class Rewind():
    def __init__(self, cfg):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        # We rewinding so...
        #cfg["feeder"]["invert"] = not cfg["feeder"]["invert"]
        self.feeder=TrinamicSilentMotor(cfg["feeder"])
        self.pickup=TrinamicSilentMotor(cfg["pickup"])
        self.pickup.disable()
        self.feeder.enable()
       
    def frameAdvance(self):
        m2=MotorThread(self.feeder,100000000)
        m2.start()
        m2.join()

import sys
h=open("hardwarecfg.json")
cfg=json.load(h)
cfg["feeder"]["invert"]= not cfg["feeder"]["invert"]
h=open("rewind.json")
rew=json.load(h)
for item in rew:
   cfg[item].update(rew[item])
reelback=Rewind(cfg)
print ("Remember to manually unaligned the left arm from its optical sensor")
print ("When you're done rewinding, just re-align the left arm to exit")
reelback.frameAdvance()
