import cv2
from picamera import PiCamera
from time import sleep
import os
from pydng import core
from Lights import Lights
from PIL import Image


lit=Lights("red")
cam=PiCamera()
sleep(4)
cam.resolution=cam.MAX_RESOLUTION
cam.iso=100
#cam.shutter_speed=12000
cam.exposure_compensation=0
cam.exposure_mode="auto"
cam.awb_mode="off";
cam.awb_gains=[1.5,1.3]
dng=core.RPICAM2DNG()
sleep(4)    

lit.set("red")
#cam.shutter_speed=12000
cam.capture("/dev/shm/pix.jpg",bayer=True)
img_r=dng.__extractRAW__("/dev/shm/pix.jpg")<<4
os.remove("/dev/shm/pix.jpg")

cam.shutter_speed=6000
lit.set("green")
cam.capture("/dev/shm/pix.jpg",bayer=True)
img_g=dng.__extractRAW__("/dev/shm/pix.jpg")<<4
os.remove("/dev/shm/pix.jpg")

lit.set("blue")
cam.capture("/dev/shm/pix.jpg",bayer=True)
img_b=dng.__extractRAW__("/dev/shm/pix.jpg")<<4
os.remove("/dev/shm/pix.jpg")

img=cv2.merge([img_b,img_g,img_r])
cv2.imwrite("test.tif",img)

lit.set("off")
