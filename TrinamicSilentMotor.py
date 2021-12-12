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
    def __init__(self,cfg,slowEnd=False,trace=False,button=None, msg=None):
        print(dumps(cfg, indent=4))
        GPIO.setmode(GPIO.BCM)
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
        self.slowEnd=slowEnd
        self.msg=msg
        self.skipHisto=2
        self.skipAdjust=0
        self.trace=trace
        self.fault=False
        self.name=cfg["name"]
        self.button=button
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

    def message(self, txt):
        if self.msg != None:
            self.msg(txt)
            

    def clearFault(self):
        self.fault=False
        self.shortsInARow=0
        
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
    def nextDelay(self):
        moveStart=self.moveStart
        now=time()
        pos=now-moveStart
        target=self.targetTime
        speed=self.speed
        speed2=self.speed2
        delta=speed-speed2        
        if pos >= target:
            newspeed=speed2
        elif pos <= (target/2):
            newspeed=speed2 + 2 * delta * pos / target
        else:
            newspeed=speed2 + 2 * delta * (target - pos) / target
        return now + (1.0/newspeed)
        
        
    def tick(self):
        if self.target != self.pos:
            self.direction()            
            return self.nextDelay()
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
        self.target= self.pos+self.faultTreshold
        self.ignore=self.ignoreInitial
        if self.learning:
            GPIO.output(self.learnPin, 1)
        if self.target < self.pos:
            self.fault=True
            raise Exception("We do not support backward yet")
        else:
            self.direction=self.forward
        self.moveStart=time()
        waitUntil=self.tick()
        while waitUntil != None:
            reading=GPIO.input(self.SensorStopPin)
            #log.append(reading)
            if self.learning and self.ignore == 5:
                GPIO.output(self.learnPin,0)
            if self.ignore > 0:
                self.ignore -= 1
            elif self.ignore == 0 and self.slowEnd:
                self.ignore = -1
                if self.skipHisto <= 0:
                    delta=time()-self.moveStart
                    self.histo.append(delta)          
            else:
                if reading == self.SensorStopState:
                    delta=time()-self.moveStart
                    if self.trace:
                        print("\033[1;32m{}\033[0m ticks for {}".format(ticks,self.name))
                    if ticks == self.ignoreInitial:
                        self.shortsInARow+= 1;
                    else:
                        self.shortsInARow=0
                    if self.shortsInARow >= 10:
                        self.fault=True
                        self.message("{} short FAULT".format(self.name))
                        raise Exception("\033[1;31mFAULT\033[0m: only the lowest amount of steps for 10 cycles in a row")
                    if self.skipHisto > 0:
                        self.skipHisto-= 1
                        return
                    if not self.slowEnd:
                        self.histo.append(delta)
                    if self.skipAdjust > 0:
                        self.skipAdjust-= 1
                        return
                    if len(self.histo)<3:
                        return
                    self.histo=self.histo[-3:]
                    avg=sum(self.histo)/len(self.histo)
                    if abs(avg-self.targetTime)<0.01:
                        return
                    gamma=2.0*(avg-self.targetTime)/(self.targetTime*100.0)
                    if gamma > 0.02:
                        gamma=0.02
                    elif gamma < -0.02:
                        gamma= -0.02
                    newspeed=self.speed * (1.0 + gamma)
                    self.speed=int(newspeed)
                    if self.speed < self.speed2:
                        self.speed=self.speed2
                        print("WARNING: speed={} and speed2={}, the fact that speed was smaller than speed2 is unexpected".format(self.speed, self.speed2))
                    elif self.speed > self.maxSpeed:
                        self.speed=self.maxSpeed
                    print("New speed for {}={}ticks/s".format(self.name, self.speed))
                    return
            delay=waitUntil - time()
            if delay>0.000001:
                sleep(delay)
            ticks+= 1
            waitUntil=self.tick()
        self.fault=True
        self.message("{} long FAULT".format(self.name))
        raise Exception("Move failed, \033[1;31m{}\033[0m passed its limit without triggering sensor".format(self.name))
