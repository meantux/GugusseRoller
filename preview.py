#!/usr/bin/python
from time import sleep
from picamera import PiCamera
from fractions import Fraction


c=PiCamera()
#c.resolution=(1024,768)
#c.resolution=(1440,1080)
c.awb_mode='off'
c.awb_gains=(1.44,1.68)
c.iso=100
c.resolution=c.MAX_RESOLUTION
c.start_preview(resolution=(1440,1080))
sleep(1)
c.exposure_mode="night"
c.iso=60
c.shutter_speed=10000
#sleep(2)
#c.capture("test.jpg")
while [1] :
    #c.led=False
    sleep(3)
    #c.led=True
    sleep(3)
#c.capture("test.jpg")
