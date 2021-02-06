#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep
from json import load
from sys import argv,exit

h=open("hardwarecfg.json","rt")
cfg=load(h)

usage="USAGE: {} <on|off>".format(argv[0])

if len(argv) < 2 or ( argv[1] != "on" and argv[1] != "off" ):
    print(usage)
    exit(0)

if argv[1] == "on":
    value=GPIO.LOW
else:
    value=GPIO.HIGH
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(cfg["filmdrive"]["pinEnable"],GPIO.OUT, initial=value)
GPIO.setup(cfg["feeder"]["pinEnable"],GPIO.OUT, initial=value)
GPIO.setup(cfg["pickup"]["pinEnable"],GPIO.OUT, initial=value)


