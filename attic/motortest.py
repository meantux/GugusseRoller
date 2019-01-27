#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep



GPIO.setmode(GPIO.BCM) 

ena=18
inv=14
stp=15

#ena=25
#inv=23
#stp=24

#ena=21
#inv=8
#stp=7


GPIO.setup(ena,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(inv,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(stp,GPIO.OUT, initial=GPIO.HIGH)

while True:
    count=5000
    GPIO.output(inv, GPIO.HIGH)
    while count > 0:
        GPIO.output(stp, GPIO.LOW)
        sleep (0.001)
        GPIO.output(stp,GPIO.HIGH)
        sleep(0.001)
        count-= 1

    count=5000
    GPIO.output(inv, GPIO.LOW)
    while count > 0:
        GPIO.output(stp, GPIO.LOW)
        sleep (0.001)
        GPIO.output(stp,GPIO.HIGH)
        sleep(0.001)
        count-= 1
    

