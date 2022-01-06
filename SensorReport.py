from threading import Thread
import RPi.GPIO as GPIO
from time import sleep
from os import nice

GPIO.setmode(GPIO.BCM)
class SensorReport(Thread):
    def __init__(self, settings, leftL, holeL, rightL, learnB):
        Thread.__init__(self)
        self.loop=True
        self.settings=settings
        self.leftL=leftL
        self.holeL=holeL
        self.rightL=rightL
        self.learnB=learnB
        self.learnDisplayed=0
        self.learnPin=settings["filmdrive"]["learnPin"]

    def checkSensor(self, pin, state, displayed, lbl):
        actual=GPIO.input(pin)
        if actual==state:
            actual=1
        else:
            actual=0
        if actual != displayed:
            if actual:
                lbl.configure(bg="white",fg="black")
            else:
                lbl.configure(bg="black",fg="white")
        return actual
            
    def toggleLearn(self):
        if self.learnDisplayed:
            GPIO.output(self.learnPin,0)
        else:
            GPIO.output(self.learnPin,1)
            
    def run(self):
        nice(19)
        self.loop=True
        lPin=self.settings["feeder"]["stopPin"]
        lState=self.settings["feeder"]["stopState"]
        lDisplayed=1-lState
        rPin=self.settings["pickup"]["stopPin"]
        rState=self.settings["pickup"]["stopState"]
        rDisplayed=1-rState
        hPin=self.settings["filmdrive"]["stopPin"]
        hState=self.settings["filmdrive"]["stopState"]
        hDisplayed=1-hState
        while self.loop:
            sleep(0.05)
            lDisplayed=self.checkSensor(
                lPin,lState,lDisplayed,self.leftL)
            rDisplayed=self.checkSensor(
                rPin,rState,rDisplayed,self.rightL)
            hDisplayed=self.checkSensor(
                hPin,hState,hDisplayed,self.holeL)
            self.learnDisplayed=self.checkSensor(
                self.learnPin,1,self.learnDisplayed, self.learnB)
        
    def stopLoop(self):
        print("Stopping sensor loop")
        self.loop=False
