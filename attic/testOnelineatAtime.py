#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) 

GPIO.setup(5,GPIO.OUT, initial=GPIO.HIGH)

import sys

lineToTest=int(sys.argv[1])

Moves=[(0,0),(0,1), (1,1), (1,0)]
class TwoPinsMotor():
    def __init__(self, pin1, pin2):
        self.pin1=pin1
        self.pin2=pin2
        self.pos=int(0)
        GPIO.setup(pin1, GPIO.OUT, initial=0)
        GPIO.setup(pin2, GPIO.OUT, initial=0)
    def forward(self):
        self.pos += 1
        states=Moves[self.pos % 4]
        GPIO.output(self.pin1, states[0])
        GPIO.output(self.pin2, states[1])
    def backward(self):
        self.pos -= 1
        states=Moves[self.pos % 4]
        GPIO.output(self.pin1, states[0])
        GPIO.output(self.pin2, states[1])
        
#motor=TwoPinsMotor(23,21)
#count=0
GPIO.setup(lineToTest, GPIO.OUT, initial=GPIO.HIGH)
while True:
    GPIO.output(lineToTest, 0)
    sleep(0.02)
    GPIO.output(lineToTest,1)
    sleep(0.02)


