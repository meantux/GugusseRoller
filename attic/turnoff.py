#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) 

GPIO.setup(18,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(25,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(21,GPIO.OUT, initial=GPIO.HIGH)


