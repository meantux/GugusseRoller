#!/usr/bin/python
################################################################################
# TrinamicSilentMotor.py
# 
#
# By: Denis-Carl Robidoux
# 3 pins motor driver for the Gugusse Roller
#
################################################################################
from time import sleep, time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) 


class TrinamicSilentMotor():
    def __init__(self,cfg):
        GPIO.setmode(GPIO.BCM)
        self.fault=False
        self.name=cfg["name"]
        self.speed=cfg["speed"]
        self.accel=cfg["accel"]
        self.currentSpeed=0
        self.target=0
        self.SensorStopPin=cfg["stopPin"]
        self.ignoreInitial=cfg["ignoreInitial"]
        self.ignore=0
        self.faultTreshold=cfg["faultTreshold"]
        self.pinEnable=cfg["pinEnable"]
        self.pinDirection=cfg["pinDirection"]
        self.pinStep=cfg["pinStep"]
        self.SensorStopState=cfg["stopState"]
        self.lasttick=time()
        self.toggle=0
        GPIO.setup(self.pinStep, GPIO.OUT, initial=0)
        GPIO.setup(self.pinEnable, GPIO.OUT, initial=0)
        if cfg["invert"]:
            GPIO.setup(self.pinDirection, GPIO.OUT, initial=0)
        else:
            GPIO.setup(self.pinDirection, GPIO.OUT, initial=1)
        self.pos=int(0)
        GPIO.setup(self.SensorStopPin, GPIO.IN)
    def enable(self):
        GPIO.output(self.pinEnable, 0)
    def disable(self):
        GPIO.output(self.pinEnable, 1)
        
    def forward(self):
        self.pos += 1
        GPIO.output(self.pinStep, self.toggle)
        if self.toggle==1:
            self.toggle=0
        else:
            self.toggle=1
    def tick(self):
        if self.target != self.pos:
            self.direction()            
            if self.currentSpeed < self.speed:
                self.currentSpeed += self.accel
            return time() + (1.0 / self.currentSpeed)
        return None
                        
    def move(self):
        ticks=0
        #log=[]
        self.target= self.pos+self.faultTreshold
        self.currentSpeed=0
        self.ignore=self.ignoreInitial
        if self.target < self.pos:
            self.fault=True
            raise Exception("We do not support backward yet")
        else:
            self.direction=self.forward
        waitUntil=self.tick()
        while waitUntil != None:
            reading=GPIO.input(self.SensorStopPin)
            #log.append(reading)
            if self.ignore > 0:
                self.ignore -= 1
            else:
                if reading == self.SensorStopState:
                    print("{} ticks for {}".format(ticks,self.name))
                    #if (self.SensorStopPin==2):
                    #    print(log)
                    return
            delay=waitUntil - time()
            if delay>0.0001:
                sleep(delay)
            ticks+= 1
            waitUntil=self.tick()
        self.fault=True
        raise Exception("Move failed, {} passed its limit without triggering sensor".format(self.name))
                


    
