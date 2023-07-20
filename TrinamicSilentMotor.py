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
from datetime import datetime
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) 
from json import dumps, dump
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon



class TrinamicSilentMotor():
    def __init__(self,cfg,trace=False, signal=None):
        print(dumps(cfg, indent=4))
        self.cfg=cfg
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
        self.isFilmDrive=cfg["isFilmDrive"]
        self.signal=signal
        self.skipHisto=2
        self.skipAdjust=0
        self.trace=trace
        self.fault=False
        self.name=cfg["name"]
        if self.isFilmDrive:
            self.move=self.moveForFilmDrive
            self.nextDelay=self.nextDelayForFilmDrive
        else:
            self.move=self.moveForTurnTables
            self.nextDelay=self.nextDelayForTurnTables
        self.SensorStopPin=cfg["stopPin"]
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
        GPIO.setup(self.SensorStopPin, GPIO.IN)
        GPIO.setup(self.pinDirection, GPIO.OUT, initial=0)
        self.log={}

    def message(self, txt):
        if self.signal != None:
            self.signal.emit(txt)
    def getConfig(self):
        return self.cfg

    def clearFault(self):
        self.fault=False
        self.shortsInARow=0
        
    def setFormat(self, cfg):
        self.speed=cfg["speed"]
        self.signal.emit(f"spdchg,{self.name},{self.speed}")
        self.speed2=cfg["speed2"]
        self.faultTreshold=cfg["faultTreshold"]
        self.ignoreInitial=cfg["ignoreInitial"]
        self.eighthPoint = self.ignoreInitial / 8.0
        self.sevenEighthPoint = 7.0 * self.ignoreInitial / 8.0
        
        
        self.targetTime=cfg["targetTime"]
        self.eighthTime = self.targetTime / 8.0
        self.sevenEighthTime = 7.0 * self.targetTime / 8.0 

        if self.isFilmDrive:
            self.halfpoint=self.ignoreInitial / 2
        else:
            self.halfTime=self.targetTime/2
                
    def enable(self):
        GPIO.output(self.pinEnable, 0)

    def disable(self):
        GPIO.output(self.pinEnable, 1)
        if self.trace and self.log != {}:
            fn=f"{datetime.now().isoformat()}-{self.name}.json"
            self.log["name"]=self.name
            with open(fn,"wt") as h:
                dump(self.log, h, indent=4)
            self.log={}


    def nextDelayForTurnTables(self):
        now = time()
        delta = now - self.moveStart

        if delta > self.targetTime:
            return now + (1.0 / self.speed2)
        if delta < self.eighthTime:
            pointSpeed = self.speed2 + (self.speed - self.speed2) * (delta / self.eighthTime)
        elif delta < self.sevenEighthTime:
            pointSpeed = self.speed
        else:
            pointSpeed = self.speed - (self.speed - self.speed2) * ((delta - self.sevenEighthTime) / self.eighthTime)

        return now + (1.0 / pointSpeed)
                

    def nextDelayForFilmDrive(self):
        now = time()

        if self.ticks > self.ignoreInitial:
            return now + (1.0 / self.speed2)
        if self.ticks <= self.eighthPoint:
            pointSpeed = self.speed2 + (self.speed - self.speed2) * (self.ticks / self.eighthPoint)
        elif self.ticks <= self.sevenEighthPoint
            pointSpeed = self.speed
        else:
            pointSpeed = self.speed - (self.speed - self.speed2) * ((self.ticks - self.sevenEighthPoint) / self.eighthPoint)
            
        return now + (1.0 / pointSpeed)
    
        
    def tick(self):
        self.ticks+= 1
        if self.ticks > self.faultTreshold:
            return None
        self.toggle=  not self.toggle
        GPIO.output(self.pinStep, self.toggle)
        return self.nextDelay()

    def getPowerState(self):
        return 1-GPIO.input(self.pinEnable)
    
    def setDirection(self, direction):
        #  I need XOR but all I got is != which
        #  does the same for booleans
        rev=False
        if direction == "ccw":
            rev=True
        if self.inverted != rev:
            GPIO.output(self.pinDirection,0)
        else:
            GPIO.output(self.pinDirection,1)
    def calculateNewSpeed(self):
        if self.skipAdjust > 0:
            self.skipAdjust-= 1
            return self.speed
        if len(self.histo)<6:
            return self.speed
        self.histo=self.histo[-6:]
        avg=sum(self.histo)/len(self.histo)
        if abs(avg-self.targetTime)<0.01:
            return self.speed
        if avg > self.targetTime:
            gamma=5.0*(avg-self.targetTime)/(self.targetTime*100.0)
        else:
            gamma=20.0*(avg-self.targetTime)/(self.targetTime*100.0)
        if gamma > 0.05:
            gamma=0.05
        elif gamma < -0.2:
            gamma= -0.2
        newspeed=self.speed * (1.0 + gamma)
        if newspeed>self.maxSpeed:
            newspeed=self.maxSpeed
        elif newspeed < self.speed2:
            newspeed=self.speed2
        self.skipAdjust=6
        self.signal.emit(f"spdchg,{self.name},{int(newspeed)}")
        return int(newspeed)
    
    def moveForTurnTables(self):
        self.ticks=0
        self.moveStart=time()
        waitUntil=self.tick()
        while waitUntil != None:
            reading=GPIO.input(self.SensorStopPin)
            if reading == self.SensorStopState:
                delta=time()-self.moveStart
                if self.ticks < self.ignoreInitial:
                    self.shortsInARow+= 1;
                else:
                    self.shortsInARow=0
                if self.shortsInARow >= 10:
                    self.fault=True
                    self.message("{} short FAULT".format(self.name))
                    raise Exception("\033[1;31mFAULT\033[0m: only the lowest amount of steps for 10 cycles in a row")
                if self.skipHisto <= 0:
                    self.histo.append(delta)
                else:
                    self.skipHisto-= 1
                self.speed=self.calculateNewSpeed()
                return
            delay=waitUntil - time()
            if delay>0.0:
                sleep(delay)

            waitUntil=self.tick()
        self.fault=True
        self.message("{} long FAULT".format(self.name))
        raise Exception("Move failed, \033[1;31m{}\033[0m passed its limit without triggering sensor".format(self.name))

    def moveForFilmDrive(self):
        self.ticks=0
        GPIO.output(self.learnPin, 1)
        self.moveStart=time()
        waitUntil=self.tick()
        pointToStopLearning=self.ignoreInitial - 5
        while waitUntil != None:
            if self.ticks == pointToStopLearning:
                GPIO.output(self.learnPin,0)
            elif self.ticks == self.ignoreInitial:
                if self.skipHisto <= 0:
                    delta=time()-self.moveStart
                    self.histo.append(delta)
                else:
                    self.skipHisto-= 1
            if self.ticks >= self.ignoreInitial and self.SensorStopState == GPIO.input(self.SensorStopPin):
                if self.ticks == self.ignoreInitial:
                    self.shortsInARow+= 1;
                else:
                    self.shortsInARow=0
                if self.shortsInARow >= 10:
                    self.fault=True
                    self.message("{} short FAULT".format(self.name))
                    raise Exception("\033[1;31mFAULT\033[0m: only the lowest amount of steps for 10 cycles in a row")
                self.speed=self.calculateNewSpeed()
                return
            delay=waitUntil - time()
            if delay>0.0:
                sleep(delay)
            waitUntil=self.tick()
            
        self.fault=True
        self.message("{} long FAULT".format(self.name))
        raise Exception("Move failed, \033[1;31m{}\033[0m passed its limit without triggering sensor".format(self.name))


class PinToggler(QThread):
    def __init__(self, pin):
        QThread.__init__(self)
        self.loop=True
        self.pin=pin
        self.toggle=GPIO.input(pin)

    def run(self):
        while self.loop:
            self.toggle= not self.toggle
            GPIO.output(self.pin, self.toggle)
            sleep(0.001)

    def killLoop(self):
        self.loop=False


class MotorManualWidget(QPushButton):
    def __init__(self, motor, direction):
        if direction=="cw":
            icon=QIcon('cw.png')
        else:
            icon=QIcon('ccw.png')
        QPushButton.__init__(self)
        self.setIcon(icon)
        self.motor=motor
        self.cfg=motor.getConfig()
        self.pin=self.cfg["pinStep"]
        self.direction=direction
        self.pressed.connect(self.startMotor)
        self.released.connect(self.stopMotor)
        self.toggler=None

    def startMotor(self):
        if self.toggler:
            self.signal.emit("Weird bug where the previous task is still there")
            return
        self.toggler=PinToggler(self.pin)
        dirval=self.cfg["invert"]
        if self.direction=="ccw":
            dirval= not dirval
        self.motor.setDirection(self.direction)
        self.toggler.start()
                
    def stopMotor(self):
        #if self.toggler:
        self.toggler.killLoop()        
        self.toggler=None
        
    
class MotorControlWidgets(QPushButton):
    signal=pyqtSignal("PyQt_PyObject")
    def __init__(self, win, cfg, trace=False):
        globalPowerIcon=QIcon('power.png')        
        QPushButton.__init__(self)
        self.name=cfg["name"]
        self.win=win
        self.setIcon(globalPowerIcon)
        self.clicked.connect(self.powerHandle)
        self.motor=TrinamicSilentMotor(cfg, trace=trace, signal=self.signal)
        self.syncMotorStatus()
        self.cw=MotorManualWidget(self.motor,"cw")
        self.ccw=MotorManualWidget(self.motor,"ccw")
        self.signal.connect(self.signalHandle)

    def syncMotorStatus(self):
        if self.motor.getPowerState():
            self.setStyleSheet("background-color: green;")
        else:
            self.setStyleSheet("background-color: grey;")

    def powerHandle(self):
        if self.motor.getPowerState():
            self.motor.disable()
        else:
            self.motor.enable()
        self.syncMotorStatus()


    def signalHandle(self, msg):
        if msg[0:6]=="spdchg":
            s=msg.split(',')
            self.win.speedmeters[s[1]].setText(f"peak: {s[2]}steps/s")
        else:
            self.win.out.append(msg)
        self.syncMotorStatus()
