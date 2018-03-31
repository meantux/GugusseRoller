#!/usr/bin/python
################################################################################
# turnoff.py
# 
#
# By: Denis-Carl Robidoux
# disables the motors
#
################################################################################

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) 

# yeah... hard-coded, I'll change that one day...
GPIO.setup(5,GPIO.OUT, initial=GPIO.LOW)


