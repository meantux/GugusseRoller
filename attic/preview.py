#!/usr/bin/python
from time import sleep
from picamera import PiCamera


c=PiCamera()
#c.resolution=(1024,768)
c.resolution=(1440,1080)
c.shutter_speed=15000
c.start_preview()
while True:
    sleep(1)
