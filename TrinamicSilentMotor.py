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
from json import dumps



class TrinamicSilentMotor():
    def __init__(self,cfg,autoSpeed=False,trace=False,button=None):
        print(dumps(cfg, indent=4))
        GPIO.setmode(GPIO.BCM)
        self.autoSpeed=autoSpeed
        if autoSpeed:
            self.minSpeed=cfg["minSpeed"]
            self.maxSpeed=cfg["maxSpeed"]
        if "learnPin" in cfg:
            self.learning=True
            self.learnPin=cfg["learnPin"]
            GPIO.setup(self.learnPin, GPIO.OUT, initial=1)
        else:
            self.learning=False
            self.learnPin= -1
        self.histo=[]
        self.skipHisto=3
        self.trace=trace
        self.fault=False
        self.name=cfg["name"]
        self.button=button
        self.currentSpeed=0
        self.target=0
        self.SensorStopPin=cfg["stopPin"]
        self.ignore=0
        self.pinEnable=cfg["pinEnable"]
        self.pinDirection=cfg["pinDirection"]
        self.pinStep=cfg["pinStep"]
        self.SensorStopState=cfg["stopState"]
        self.inverted=cfg["invert"]
        self.lasttick=time()
        self.toggle=0
        self.shortsInARow=0
        GPIO.setup(self.pinStep, GPIO.OUT, initial=0)
        GPIO.setup(self.pinEnable, GPIO.OUT, initial=0)
        self.pos=int(0)
        GPIO.setup(self.SensorStopPin, GPIO.IN)

    def setFormat(self, cfg):
        self.speed=cfg["speed"]
        self.speed2=cfg["speed2"]
        self.accel=cfg["accel"]
        self.ignoreInitial=cfg["ignoreInitial"]
        self.faultTreshold=cfg["faultTreshold"]
        if "targetTime" in cfg:
            self.targetTime=cfg["targetTime"]
                
    def enable(self):
        GPIO.output(self.pinEnable, 0)
        if self.button:
            self.button.configure(bg="green")
    def disable(self):
        GPIO.output(self.pinEnable, 1)
        if self.button:
            self.button.configure(bg="grey")
        
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
            if self.currentSpeed < self.targetSpeed:
                self.currentSpeed += self.accel
                if self.currentSpeed > self.targetSpeed:
                    self.currentSpeed=self.targetSpeed
            return time() + (1.0 / self.currentSpeed)
        return None

    def getPowerState(self):
        return GPIO.input(self.pinEnable)
    
    def setDirection(self, direction):
        #  I need XOR but all I got is != which
        #  does the same for booleans
        rev=False
        if direction == "ccw":
            rev=True
        elif direction != "cw":
            raise Exception("Bad direction parameter")        
        if self.inverted != rev:
            GPIO.setup(self.pinDirection, GPIO.OUT, initial=0)
        else:
            GPIO.setup(self.pinDirection, GPIO.OUT, initial=1)
        
    def blindMove(self, ticks):
        delay=0.020
        while ticks > 0:
            sleep(delay)
            if delay > 0.001:
                delay-= 0.0005
            self.forward()
            ticks-= 1
            
    def move(self):
        ticks=0
        #log=[]
        if self.autoSpeed:
            self.moveStart=time()
        self.target= self.pos+self.faultTreshold
        self.targetSpeed=self.speed
        self.currentSpeed=0
        self.ignore=self.ignoreInitial
        if self.learning:
            GPIO.output(self.learnPin, 1)
        if self.target < self.pos:
            self.fault=True
            raise Exception("We do not support backward yet")
        else:
            self.direction=self.forward
        waitUntil=self.tick()
        while waitUntil != None:
            reading=GPIO.input(self.SensorStopPin)
            #log.append(reading)
            if self.learning and self.ignore == 5:
                GPIO.output(self.learnPin,0)
            if self.ignore > 0:
                self.ignore -= 1
            else:
                if reading == self.SensorStopState:
                    if self.trace:
                        print("\033[1;32m{}\033[0m ticks for {}".format(ticks,self.name))
                    if ticks == self.ignoreInitial:
                        self.shortsInARow+= 1;
                    else:
                        self.shortsInARow=0
                    if self.shortsInARow >= 10:
                        self.fault=True
                        raise Exception("\033[1;31mFAULT\033[0m: only the lowest amount of steps for 10 cycles in a row")
                    if self.autoSpeed:
                        if self.skipHisto > 0:
                            self.skipHisto-= 1
                            return
                        delta=time()-self.moveStart
                        self.histo.append(delta)
                        if len(self.histo)<3:
                            return
                        self.histo=self.histo[-3:]
                        avg=sum(self.histo)/len(self.histo)
                        if abs(avg-self.targetTime)<0.001:
                            return
                        gamma=10.0*(avg-self.targetTime)/(self.targetTime*100.0)
                        newspeed=self.speed2 * (1.0 + gamma)
                        self.speed2=int(newspeed)
                        if self.speed2 < self.minSpeed:
                            self.speed2=self.minSpeed
                        elif self.speed2 > self.maxSpeed:
                            self.speed2=self.maxSpeed
                        self.speed=self.speed2
                        print("New speed for {}={}ticks/s".format(self.name, self.speed))
                    return
            if self.ignore == 0 and self.ignoreInitial != 0:
                self.currentSpeed=self.speed2
                self.targetSpeed=self.speed2
            delay=waitUntil - time()
            if delay>0.000001:
                sleep(delay)
            ticks+= 1
            waitUntil=self.tick()
        self.fault=True
        raise Exception("Move failed, \033[1;31m{}\033[0m passed its limit without triggering sensor".format(self.name))
