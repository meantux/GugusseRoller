import json
from picamera import PiCamera



class GCamera(PiCamera):
    def __init__(self, fn="cameraSettings.json"):        
        PiCamera.__init__(self)
        with open(fn, "r") as h:
            self.settings=json.load(h)
        self.resolution=self.MAX_RESOLUTION
        self.applySettings()
        self.start_preview(fullscreen=False,resolution=(1024,768),window=(256,0,1024,768))
        self.camModes=[ "off", "auto", "night", "nightpreview", "backlight", "spotlight", "sports", "snow", "beach", "verylong", "fixedfps", "antishake", "fireworks"]
        self.awbModes=[ "off", "auto", "sunlight", "cloudy", "shade", "tungsten", "fluorescent", "incandescent", "flash", "horizon"]
        self.meterModes=[ "average", "spot", "backlit", "matrix" ]
        self.zooms=[(0.0,0.0,1.0,1.0), (0.0,0.0,0.333,0.333), (0.333,0.0,0.333,0.333), (0.667,0.0,0.333,0.333), (0.0,0.333,0.333,0.333), (0.333,0.333,0.333,0.333), (0.667,0.333,0.333,0.333), (0.0,0.667,0.333,0.333), (0.333,0.667,0.333,0.333), (0.667,0.667,0.333,0.333)]

    def saveSettings(self, fn="cameraSettings.json"):
        with open(fn, "w") as h:
            json.dump(self.settings, h, indent=4)

    def selectOther(self, actual, choices, direction):
        idx=choices.index(actual)
        idx+= direction
        if idx < 0:
            idx=len(choices)-1
        elif idx >= len(choices):
            idx=0
        return choices[idx]
        
    def freezeWhiteBalance(self):
        if self.settings["awb_mode"] != "auto":
            print("Need to be in auto to freeze")
            return
        values=self.awb_gains
        a=float(values[0])
        b=float(values[1])
        print("a={}".format(a))
        print("b={}".format(b))
        self.settings["awb_gains"]=[a,b]
        self.awb_mode="off"
        self.settings["awb_mode"]="off"
        self.saveSettings()
        return [a,b]

    def applySettings(self, settings=None):
        if settings != None:
            self.settings=settings
        s=self.settings
        self.exposure_mode=s["exposure_mode"]
        self.iso=s["iso"]
        self.shutter_speed=s["shutter_speed"]
        self.exposure_compensation=s["exposure_compensation"]
        self.awb_mode=s["awb_mode"]
        if s["awb_mode"] == "off":
            self.awb_gains=s["awb_gains"]
        self.brightness=s["brightness"]
        self.contrast=s["contrast"]
