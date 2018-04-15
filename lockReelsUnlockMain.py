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


class Lock():
    def __init__(self, cfg):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        # We rewinding so...
        self.enablePin=cfg["motorEnablePin"]
        GPIO.setup(self.enablePin, GPIO.OUT, initial=1)
        for pin in cfg["filmdrive"]["pins"]:
           GPIO.setup(pin, GPIO.OUT, initial=0)
        alternate=0
        for pin in cfg["feeder"]["pins"]:
           GPIO.setup(pin, GPIO.OUT, initial=alternate % 2)
           sleep (0.1)
           alternate+= 1
        for pin in cfg["pickup"]["pins"]:
           GPIO.setup(pin, GPIO.OUT, initial=alternate % 2)
           sleep (0.1)
           alternate+= 1
         
       
    def frameAdvance(self):
        m2=MotorThread(self.feeder,100000000)
        m2.start()
        m2.join()
        
import sys
try:
   h=open(sys.argv[1])
   cfg=json.load(h)
except Exception as e:
   print (e.message)
   print ("\nUSAGE: {} <motor json file>\n".format(sys.argv[0]))
   sys.exit(0)

Lock(cfg)
