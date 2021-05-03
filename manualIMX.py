#!/usr/bin/python3

from array import array
import cv2
import numpy as np
from Lights import Lights
from ICamera import ICamera



mode="full"
cam=ICamera()
lit=Lights("green")
offsetX=int((cam.w-cam.ww)/2)
offsetY=int((cam.h-cam.wh)/2)
while True:
    img=cam.captureOnePicture()
    key=cv2.waitKey(20)
    if key == 255 or key == -1:
        pass
    elif key == ord('m'):
        if mode == "full":
            mode="zoom"
        else:
            mode="full"
    elif key == ord('s'):
        offsetY+= int(cam.wh/2)
        if offsetY >= (cam.h-cam.wh):
            offsetY = cam.h-cam.wh-1
    elif key == ord('w'):
        offsetY-= int(cam.wh/2)
        if offsetY < 0:
            offsetY=0
    elif key == ord('a'):
        offsetX-= int(cam.ww/2)
        if offsetX < 0:
            offsetX = 0
    elif key == ord('d'):
        offsetX+= int(cam.ww/2)
        if offsetX >= (cam.w-cam.ww):
            offsetX = cam.w - cam.ww - 1
    elif key == 27:
        break
    else:
        print("Key {} was pressed".format(key))
    if mode=="full":
        res=cv2.resize(img,(cam.ww,cam.wh),interpolation=cv2.INTER_LINEAR)
    elif mode == "zoom":
        res=img[offsetY:offsetY+cam.wh,offsetX:offsetX+cam.ww]
    else:
        print("Wut?")
        break    
    cam.showPix(res)





