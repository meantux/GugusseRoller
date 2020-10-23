#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep
from json import load
from sys import argv,exit

h=open("hardwarecfg.json","rt")
cfg=load(h)

usage="USAGE: {} <on|off|red|green|blue|cyan|magenta|yellow>".format(argv[0])

up=GPIO.HIGH
dn=GPIO.LOW


tab={
    "on":[up,up,up],
    "off":[dn,dn,dn],
    "red":[up,dn,dn],
    "green":[dn,up,dn],
    "blue":[dn,dn,up],
    "cyan":[dn,up,up],
    "magenta":[up,dn,up],
    "yellow":[up,up,dn]
}

if len(argv) < 2 or argv[1] not in tab:
    print(usage)
    exit(0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(cfg["lights"]["red"],GPIO.OUT,initial=tab[argv[1]][0])
GPIO.setup(cfg["lights"]["green"],GPIO.OUT,initial=tab[argv[1]][1])
GPIO.setup(cfg["lights"]["blue"],GPIO.OUT,initial=tab[argv[1]][2])

