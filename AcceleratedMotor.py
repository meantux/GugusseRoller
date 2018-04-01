#!/usr/bin/python
################################################################################
# AcceleratedMotor.py
# 
#
# By: Denis-Carl Robidoux
# 4 pins motor driver for the Gugusse Roller
#
################################################################################
from time import sleep, time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) 


class AcceleratedMotor():
    Reverse=[(1,0),(0,1),(3,0),(2,1),(0,0),(1,1),(2,0),(3,1)]
    Normal= [(1,1),(3,0),(2,1),(1,0),(0,1),(2,0),(3,1),(0,0)]
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
        self.SensorStopState=cfg["stopState"]
        self.pins=cfg["pins"]
        self.lasttick=time()
        if cfg["invert"]:
            self.order=self.Reverse
        else:
            self.order=self.Normal
        self.pos=int(0)
        GPIO.setup(self.pins[0], GPIO.OUT, initial=0)
        GPIO.setup(self.pins[1], GPIO.OUT, initial=1)
        GPIO.setup(self.pins[2], GPIO.OUT, initial=0)
        GPIO.setup(self.pins[3], GPIO.OUT, initial=1)
        GPIO.setup(self.SensorStopPin, GPIO.IN)
        
    def forward(self):
        self.pos += 1
        states=self.order[self.pos % 8]
        GPIO.output(self.pins[states[0]], states[1])
    def tick(self):
        if self.target != self.pos:
            self.direction()            
            if self.currentSpeed < self.speed:
                self.currentSpeed += self.accel
            return time() + (1.0 / self.speed)
        return None
                        
    def setMove(self, quantity):
        ticks=0
        log=[]
        self.target= self.pos+quantity
        self.currentSpeed=0
        self.ignore=self.ignoreInitial
        if self.target < self.pos:
            self.fault=True:
            raise Exception("We do not support backward yet")
        else:
            self.direction=self.forward
        waitUntil=self.tick()
        while waitUntil != None:
            reading=GPIO.input(self.SensorStopPin)
            log.append(reading)
            if self.ignore > 0:
                self.ignore -= 1
            else:
                if reading == self.SensorStopState:
                    print("{} ticks for {}".format(ticks,self.name))
                    if (self.SensorStopPin==2):
                        print(log)
                    return
            delay=waitUntil - time()
            if delay>0.0001:
                sleep(delay)
            ticks+= 1
            waitUntil=self.tick()
        self.fault=True
        raise Exception("Move failed, {} passed its limit without triggering sensor".format(self.name))
                


    
