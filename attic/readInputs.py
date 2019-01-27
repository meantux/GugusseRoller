#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) 

#GPIO.setup(5,GPIO.OUT, initial=GPIO.HIGH)


GPIO.setup(2,GPIO.IN)
GPIO.setup(3,GPIO.IN)
GPIO.setup(5,GPIO.IN)


while True:
    print("{}-{}-{}".format(GPIO.input(2),GPIO.input(3),GPIO.input(5)))
    sleep (0.01)

