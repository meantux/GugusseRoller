import json
from picamera import PiCamera
from time import sleep
import os
from pydng.core import RPICAM2DNG

class GCamera(PiCamera):
    def __init__(self, framecount=0, fn="cameraSettings.json"):
        self.framecount=framecount
        PiCamera.__init__(self)
        with open(fn, "r") as h:
            self.gcSettings=json.load(h)
        with open("captureModes.json","r") as h:
            self.captureModes=json.load(h)
        with open("previewSettings.json","r") as p:
            self.previewSettings=json.load(p)
            p=self.previewSettings
        self.resolution=self.MAX_RESOLUTION
        self.start_preview(fullscreen=False,resolution=(p["width"],p["height"]),window=(p["offsetX"],p["offsetY"],p["width"],p["height"]),vflip=False,hflip=False)
        self.gcCamModes=[ "off", "auto", "night", "nightpreview", "backlight", "spotlight", "sports", "snow", "beach", "verylong", "fixedfps", "antishake", "fireworks"]
        self.gcAwbModes=[ "off", "auto", "sunlight", "cloudy", "shade", "tungsten", "fluorescent", "incandescent", "flash", "horizon"]
        self.gcMeterModes=[ "average", "spot", "backlit", "matrix" ]
        self.gcZooms=[(0.0,0.0,1.0,1.0), (0.0,0.0,0.333,0.333), (0.333,0.0,0.333,0.333), (0.667,0.0,0.333,0.333), (0.0,0.333,0.333,0.333), (0.333,0.333,0.333,0.333), (0.667,0.333,0.333,0.333), (0.0,0.667,0.333,0.333), (0.333,0.667,0.333,0.333), (0.667,0.667,0.333,0.333)]
        # As recommended by the documentation on the raspberri pi camera
        # we have to leave it in automatic a few seconds before setting
        # up manual values.
        sleep (4)
        self.gcApplySettings()
        self.captureMode=self.gcSettings["captureMode"]
        self.suffix=self.captureModes[self.captureMode]["suffix"]
        self.DNG=RPICAM2DNG()
        
    def gcSaveSettings(self, fn="cameraSettings.json"):
        with open(fn, "w") as h:
            json.dump(self.gcSettings, h, indent=4)

    def selectOther(self, actual, choices, direction):
        idx=choices.index(actual)
        idx+= direction
        if idx < 0:
            idx=len(choices)-1
        elif idx >= len(choices):
            idx=0
        return choices[idx]
        
    def freezeWhiteBalance(self):
        if self.gcSettings["awb_mode"] != "auto":
            print("AWB needs to be in auto to freeze")
            return
        values=self.awb_gains
        a=float(values[0])
        b=float(values[1])
        print("a={}".format(a))
        print("b={}".format(b))
        self.gcSettings["awb_gains"]=[a,b]
        self.awb_mode="off"
        self.gcSettings["awb_mode"]="off"
        self.gcSaveSettings()
        return [a,b]

    def gcApplySettings(self, settings=None):
        if settings != None:
            self.gcSettings=settings
        s=self.gcSettings
        self.exposure_mode=s["exposure_mode"]
        self.iso=s["iso"]
        if s["exposure_mode"] == "off":
            self.shutter_speed=int(s["shutter_speed"])
            self.exposure_compensation=0
        else:
            self.shutter_speed=int(0)
            self.exposure_compensation=s["exposure_compensation"]
            
        self.awb_mode=s["awb_mode"]
        if s["awb_mode"] == "off":
            self.awb_gains=s["awb_gains"]
        self.brightness=s["brightness"]
        self.contrast=s["contrast"]
    def captureCycle(self):
        if self.captureMode == "singleJpg":
            fn="/dev/shm/{:05d}.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}.jpg".format(self.framecount)
            self.capture(fn)
            os.rename(fn, fnComplete)            

        elif self.captureMode == "bracketing":
            fn="/dev/shm/{:05d}_m.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_m.jpg".format(self.framecount)
            self.capture(fn)
            self.shutter_speed=int(self.gcSettings["shutter_speed"]/2)
            os.rename(fn, fnComplete)
            sleep(1)
            fn="/dev/shm/{:05d}_l.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_l.jpg".format(self.framecount)
            self.capture(fn)
            self.shutter_speed=int(self.gcSettings["shutter_speed"]*2)
            os.rename(fn, fnComplete)
            sleep(1)
            fn="/dev/shm/{:05d}_h.jpg".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}_h.jpg".format(self.framecount)
            self.capture(fn)
            os.rename(fn, fnComplete)                     
            self.shutter_speed=int(self.gcSettings["shutter_speed"])
            
        elif self.captureMode == "PyDNG":
            fn="/dev/shm/{:05d}.jpg".format(self.framecount)
            fnSecond="/dev/shm/{:05d}.dng".format(self.framecount)
            fnComplete="/dev/shm/complete/{:05d}.dng".format(self.framecount)
            self.capture(fn, bayer=True)
            self.DNG.convert(fn,process=False, compress=False)
            os.rename(fnSecond, fnComplete)
            os.remove(fn)

        self.framecount+= 1
