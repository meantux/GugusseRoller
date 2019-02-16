#!/usr/bin/python
from time import sleep
from picamera import PiCamera
from fractions import Fraction


c=PiCamera()
#c.resolution=(1024,768)
#c.resolution=(1440,1080)
#c.awb_mode='off'
#c.awb_gains=(Fraction(229,256),Fraction(763,256))
#c.iso=100
c.start_preview()
#sleep(1)
#c.exposure_mode="off"
#c.iso=25
#c.shutter_speed=8000
#sleep(2)
#c.capture("test.jpg")
while [1] :
    #c.led=False
    sleep(3)
    #c.led=True
    sleep(3)
#c.capture("test.jpg")
