#!/usr/bin/python
from time import sleep
from picamera import PiCamera
from fractions import Fraction


c=PiCamera()
#c.resolution=(1024,768)
#c.resolution=(1440,1080)
c.shutter_speed=int(16600*2.0)
#c.awb_mode='off'
#c.awb_gains=(Fraction(229,256),Fraction(763,256))
c.start_preview()
while [1] :
    sleep(1)
#c.capture("test.jpg")
