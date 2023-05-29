#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep
from json import load
from sys import argv,exit

from PyQt5.QtWidgets import QComboBox, QLabel

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

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


class Lights():
    def __init__(self, state="off"):        
        h=open("hardwarecfg.json","rt")
        self.cfg=load(h)
        GPIO.setup(self.cfg["lights"]["red"],GPIO.OUT,initial=tab[state][0])
        GPIO.setup(self.cfg["lights"]["green"],GPIO.OUT,initial=tab[state][1])
        GPIO.setup(self.cfg["lights"]["blue"],GPIO.OUT,initial=tab[state][2])

    def set(self, state):
        GPIO.output(self.cfg["lights"]["red"],tab[state][0])
        GPIO.output(self.cfg["lights"]["green"],tab[state][1])
        GPIO.output(self.cfg["lights"]["blue"],tab[state][2])
        
    def getOptions(self):
        return tab.keys()

class LightControlWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        self.win=win
        self.lights=Lights()
        self.addItems(self.lights.getOptions())
        self.lights.set("on")
        self.setCurrentText("on")
        self.currentTextChanged.connect(self.handle)
        self.label=QLabel("Lights")

    def handle(self, text):
        self.lights.set(text)

    def getLabel(self):
        return self.label

if __name__=="__main__":
    usage="USAGE: {} <on|off|red|green|blue|cyan|magenta|yellow>".format(argv[0])
    if len(argv) < 2 or argv[1] not in tab:
        print(usage)
        exit(0)
    l=Lights(argv[1])
