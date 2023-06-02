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
        
        self.preview_config=self.create_preview_configuration(main={"size":(4056,3040)},controls={"FrameRate":self.fps,"FrameDurationLimits": (1000, 1000000//self.fps),"NoiseReductionMode":0},raw={'format': 'SBGGR12_CSI2P', 'size': (4056, 3040)},transform=transform)
        self.still_config=self.create_still_configuration(display=None, raw={},controls={"FrameRate":self.fps,"FrameDurationLimits": (1000, 1000000//self.fps),"NoiseReductionMode":0})
        
        print(self.preview_config)
        print(self.still_config)
        self.configure(self.preview_config)        
    def createPreviewWidget(self):
        self.camWidget=CameraSettings.previewWindowWidget(self.win)
            
    def setFileIndex(self, newIndex):
        self.framecount=newIndex
        
    def captureCycle(self):
        captureMode=self.win.captureMode.currentText()
        if captureMode == "singleJpg":
            fn="/dev/shm/{:05d}.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}.jpg".format(self.framecount)
            #self.switch_mode_and_capture_file(self.still_config, fn)
            buffers,metadata=self.capture_buffers(["main"])
            orig=self.helpers.make_image(buffers[0], self.preview_config["main"]).convert('RGB')
            orig.save(fn)
            os.rename(fn,fnComplete)

        elif captureMode == "bracketing":
            shutter=self.win.settings["ExposureMicroseconds"]
            fps=self.win.settings["fps"]            
            fn="/dev/shm/{:05d}_m.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_m.jpg".format(self.framecount)
            self.switch_mode_and_capture_file(self.still_config, fn)
            self.shutter_speed=int(shutter/2)
            os.rename(fn, fnComplete)
            sleep(3.0/float(fps))
            fn="/dev/shm/{:05d}_l.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_l.jpg".format(self.framecount)
            self.switch_mode_and_capture_file(self.still_config, fn)
            self.shutter_speed=int(shutter*2)
            os.rename(fn, fnComplete)
            sleep(3.0/float(fps))
            fn="/dev/shm/{:05d}_h.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_h.jpg".format(self.framecount)
            self.switch_mode_and_capture_file(self.still_config, fn)
            os.rename(fn, fnComplete)                     
            self.shutter_speed=int(shutter)
            
        elif captureMode == "DNG":
            fn="/dev/shm/{:05d}.dng".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}.dng".format(self.framecount)
            self.switch_mode_and_capture_file(self.still_config, fn)
            os.rename(fn, fnComplete)
            os.remove(fn)
                          
        self.framecount+= 1
        print ("Next:{}".format(self.framecount)) 
