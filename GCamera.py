import json
from picamera import PiCamera
from time import sleep


class GCamera(PiCamera):
    def __init__(self, fn="cameraSettings.json"):        
        PiCamera.__init__(self)
        with open(fn, "r") as h:
            self.gcSettings=json.load(h)
        self.resolution=self.MAX_RESOLUTION
        self.start_preview(fullscreen=False,resolution=(1024,768),window=(256,0,1024,768))
        self.gcCamModes=[ "off", "auto", "night", "nightpreview", "backlight", "spotlight", "sports", "snow", "beach", "verylong", "fixedfps", "antishake", "fireworks"]
        self.gcAwbModes=[ "off", "auto", "sunlight", "cloudy", "shade", "tungsten", "fluorescent", "incandescent", "flash", "horizon"]
        self.gcMeterModes=[ "average", "spot", "backlit", "matrix" ]
        self.gcZooms=[(0.0,0.0,1.0,1.0), (0.0,0.0,0.333,0.333), (0.333,0.0,0.333,0.333), (0.667,0.0,0.333,0.333), (0.0,0.333,0.333,0.333), (0.333,0.333,0.333,0.333), (0.667,0.333,0.333,0.333), (0.0,0.667,0.333,0.333), (0.333,0.667,0.333,0.333), (0.667,0.667,0.333,0.333)]
        # As recommended by the documentation on the raspberri pi camera
        # we have to leave it in automatic a few seconds before setting
        # up manual values.
        sleep (4)
        self.gcApplySettings()

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
            print("Need to be in auto to freeze")
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
        self.shutter_speed=s["shutter_speed"]
        self.exposure_compensation=s["exposure_compensation"]
        self.awb_mode=s["awb_mode"]
        if s["awb_mode"] == "off":
            self.awb_gains=s["awb_gains"]
        self.brightness=s["brightness"]
        self.contrast=s["contrast"]
