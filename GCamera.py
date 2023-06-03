import json
from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2
from time import sleep, time
import os
from threading import Thread
import CameraSettings
from libcamera import Transform



defaultValues={
    "fps":10
}
def setMissingToDefault(settings):
    for key in defaultValues:
        if key not in settings:
            settings[key]=defaultValues[key]

class GCamera(Picamera2):
    def __init__(self, win):
        Picamera2.__init__(self)
        self.win=win
        setMissingToDefault(win.settings)
        self.framecount=0
        with open("captureModes.json","r") as h:
            self.captureModes=json.load(h)

        self.fps=win.settings["fps"]
        vflip=False
        hflip=False
        if "hflip" in win.settings:
            hflip=win.settings["hflip"]        
        if "vflip" in win.settings:
            vflip=win.settings["vflip"]
        transform=Transform(vflip=vflip,hflip=hflip)
        
        self.config=self.create_preview_configuration(main={"size":self.sensor_resolution},controls={"FrameRate":self.fps,"FrameDurationLimits": (1000, 1000000//self.fps),"NoiseReductionMode":0},raw={'size':self.sensor_resolution},transform=transform)
        
        print(self.config)
        self.configure(self.config)

    def getConfig(self):
        return self.config
    
    def createPreviewWidget(self):
        self.camWidget=CameraSettings.previewWindowWidget(self.win)
            
    def setFileIndex(self, newIndex):
        self.framecount=newIndex
        
    def captureCycle(self):
        captureMode=self.win.captureMode.currentText()
        if captureMode == "singleJpg":
            fn="/dev/shm/{:05d}.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}.jpg".format(self.framecount)
            buffers,metadata=self.capture_buffers(["main"])
            orig=self.helpers.make_image(buffers[0], self.config["main"]).convert('RGB')
            orig.save(fn)
            os.rename(fn,fnComplete)

        elif captureMode == "bracketing":
            shutter=self.win.settings["ExposureMicroseconds"]
            fps=self.win.settings["fps"]            
            fn="/dev/shm/{:05d}_m.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_m.jpg".format(self.framecount)
            buffers,metadata=self.capture_buffers(["main"])
            orig=self.helpers.make_image(buffers[0], self.config["main"]).convert('RGB')
            orig.save(fn)
            self.shutter_speed=int(shutter/2)
            os.rename(fn, fnComplete)
            sleep(3.0/float(fps))
            fn="/dev/shm/{:05d}_l.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_l.jpg".format(self.framecount)
            buffers,metadata=self.capture_buffers(["main"])
            orig=self.helpers.make_image(buffers[0], self.config["main"]).convert('RGB')
            orig.save(fn)
            self.shutter_speed=int(shutter*2)
            os.rename(fn, fnComplete)
            sleep(3.0/float(fps))
            fn="/dev/shm/{:05d}_h.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_h.jpg".format(self.framecount)
            buffers,metadata=self.capture_buffers(["main"])
            orig=self.helpers.make_image(buffers[0], self.config["main"]).convert('RGB')
            orig.save(fn)
            os.rename(fn, fnComplete)                     
            self.shutter_speed=int(shutter)
            
        elif captureMode == "DNG":
            fn=f"/dev/shm/{self.framecount:05d}.dng"
            fnComplete=f"/dev/shm/complete/{self.framecount:05d}.dng"
            buffers,metadata=self.capture_buffers(["raw"])
            self.helpers.save_dng(buffers[0],metadata, self.config["raw"], fn)
            os.rename(fn, fnComplete)
                          
        self.framecount+= 1
