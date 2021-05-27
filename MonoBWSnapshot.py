import cv2
from picamera import PiCamera
from time import sleep
import os
from pydng import core
from Lights import Lights
from PIL import Image

lit=Lights("on")
cam=PiCamera()
sleep(4)
cam.resolution=cam.MAX_RESOLUTION
cam.iso=100
cam.shutter_speed=6000
cam.exposure_compensation=0
cam.awb_mode="off";
cam.awb_gains=[1.5,1.3]
dng=core.RPICAM2DNG()
sleep(4)
def snapshot(color):
    print("doing color {}".format(color))
    lit.set(color)
    sleep(0.1)
    cam.capture("/dev/shm/pix.jpg",bayer=True)
    img=dng.__extractRAW__("/dev/shm/pix.jpg")<<4
    os.remove("/dev/shm/pix.jpg")
    return img
    #cv2.imwrite("{}.tif".format(color),img)

red=snapshot("red")
green=snapshot("green")
blue=snapshot("blue")
image=cv2.merge([blue, green, red])
cv2.imwrite("test.tif", image)
#snapshot("on")
    
lit.set("off")
