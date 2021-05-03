#!/usr/bin/python3.8

import json
from picamera import PiCamera
from time import sleep
import os
import shutil
from array import array
import cv2
import numpy as np
from Lights import Lights

class ICamera(PiCamera):
    def __init__(self, framecount=0, fn="cameraSettings.json", cfg="imx183Settings.json"):
        self.framecount=framecount
        h=open(cfg, "rt")
        settings=json.load(h)
        h.close()
        self.w=settings["camera"]["width"]
        self.h=settings["camera"]["height"]
        self.ww=settings["preview"]["width"]
        self.wh=settings["preview"]["height"]
        self.cam=open(settings["camera"]["deviceFile"],"rb")
        cv2.namedWindow("Gugusse",1)
        cv2.waitKey(1000)
        self.light=Lights("on")
        
        
    def selectOther(self, actual, choices, direction):
        idx=choices.index(actual)
        idx+= direction
        if idx < 0:
            idx=len(choices)-1
        elif idx >= len(choices):
            idx=0
        return choices[idx]
        
    def freezeWhiteBalance(self):
        pass
    def gcApplySettings(self, settings=None):
        pass
    def captureOnePicture(self):
        a=array('H')
        a.fromfile(self.cam, self.h*self.w)
        n=np.array(a)
        n=n<<4
        img=n.reshape(self.h,self.w,1)
        #img2=img[968:2968,1344:4344]
        return cv2.flip(img,0)
    
    def showPix(self, img):
        cv2.imshow("Gugusse", img)
                
    def captureCycle(self):        
        self.light.set("red")
        self.captureOnePicture()
        cv2.waitKey(10)
        self.light.set("green")
        self.captureOnePicture()
        cv2.waitKey(10)
        self.light.set("blue")
        r=self.captureOnePicture()
        cv2.waitKey(10)
        self.light.set("on")
        g=self.captureOnePicture()
        cv2.waitKey(10)
        b=self.captureOnePicture()
        img=cv2.merge([b,g,r])
        fn="/dev/shm/{:05d}.tif".format(self.framecount)
        fnComplete="/dev/shm/complete/{:05d}.tif".format(self.framecount)
        cv2.imwrite(fn, img)
        os.rename(fn, fnComplete)            
        res=cv2.resize(img,(self.ww,self.wh),interpolation=cv2.INTER_LINEAR)
        cv2.imshow("Gugusse", res)
        cv2.waitKey(10)
        self.framecount+= 1
        print ("Next:{}".format(self.framecount)) 
        
if __name__ == "__main__":
    cam=ICamera()
    cam.captureCycle()
    shutil.move("/dev/shm/complete/00000.tif","/home/pi/00000.tif")
    
