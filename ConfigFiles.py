import json
import shutil


class ConfigFiles(dict):
    def __init__(self, filename):
        self.filename=filename
        self.config={
            "ftp.json": self.getDefaultFtpSettings,
            "GugusseSettings.json": self.getDefaultGugusseSettings,
            "hardwarecfg.json": self.getDefaultHardwareSettings,
            "captureModes.json" : self.getDefaultCaptureModes
        }
        try:
            with open(filename, "rt") as h:
                data=json.load(h)
        except:
            data=self.config[filename]()
            with open(filename, "wt") as h:
                json.dump(data, h, indent=4)
        super(ConfigFiles, self).__init__(data)
    def save(self):
        with open(f"_{self.filename}", "wt") as h:
            json.dump(dict(self), h, sort_keys=True, indent=4)
        shutil.move(f"_{self.filename}",self.filename)
                
    def getDefaultFtpSettings(self):
         return {
             "passwd":"",
             "path":"",
             "server":"",
             "user":""
         }
         
    def getDefaultGugusseSettings(self):
        return {
            "fps": 10,
            "ExposureMicroseconds": 30000,
            "ExposureCompensationStops": 0.0,
            "Exposure": "Manual",
            "ISO": 100,
            "WhiteBalanceMode": "Manual",
            "RedGain": 2.2,
            "BlueGain": 2.1,
            "WhileBalanceMode": "Auto",
            "vflip": False,
            "hflip": False,
            "ReelsDirection": "cw",
            "CaptureMode": "DNG"
        }

    def getDefaultCaptureModes(self):
        return {
            "DNG": {
                "description":"12bits DNGs",
                "suffix":"dng",
            },
            "singleJpg":{
                "description":"simple jpg",
                "suffix":"jpg",
            },   
            "bracketing":{
                "description":"Bracketing (0,+1,-1) JPGs ",
                "suffix":"jpg",
            }
        }

    def getDefaultHardwareSettings(self):
        return {
            "feeder": {
                "DefaultTargetTime": 0.25,
                "invert": False,
                "maxSpeed": 20000,
                "minSpeed": 20,
                "name": "feeder",
                "pinDirection": 23,
                "pinEnable": 25,
                "pinStep": 24,
                "slowEnd": False,
                "stopPin": 6,
                "stopState": 1
            },
            "filmFormats": {
                "16mm": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 2000.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    },
                    "filmdrive": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 1800,
                        "speed": 9000.0,
                        "speed2": 100.0,
                        "targetTime": 0.55
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 2000.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    }
                },
                "16mmBigReels": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    },
                    "filmdrive": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 1800,
                        "speed": 9000.0,
                        "speed2": 100.0,
                        "targetTime": 0.55
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 2000.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    }
                },
                "35mm": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 2500.0,
                        "speed2": 500.0,
                        "targetTime": 0.8
                    },
                    "filmdrive": {
                        "faultTreshold": 15000,
                        "ignoreInitial": 4650,
                        "speed": 15000.0,
                        "speed2": 200.0,
                        "targetTime": 1.0
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 4000.0,
                        "speed2": 500.0,
                        "targetTime": 0.8
                    }
                },
                "35mmBigReels": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 400.0,
                        "speed2": 100.0,
                        "targetTime": 0.7
                    },
                    "filmdrive": {
                        "faultTreshold": 15000,
                        "ignoreInitial": 4650,
                        "speed": 15000.0,
                        "speed2": 200.0,
                        "targetTime": 1.0
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 700.0,
                        "speed2": 100.0,
                        "targetTime": 0.7
                    }
                },
                "35mmSoundtrack": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 400.0,
                        "speed2": 400.0,
                        "targetTime": 0.15
                    },
                    "filmdrive": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 1100,
                        "speed": 2000.0,
                        "speed2": 200.0,
                        "targetTime": 0.4
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 20,
                        "speed": 400.0,
                        "speed2": 400.0,
                        "targetTime": 0.15
                    }
                },
                "8mm": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    },
                    "filmdrive": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 860,
                        "speed": 8000.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    }
                },
                "pathex": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.5
                    },
                    "filmdrive": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 1800,
                        "speed": 12000.0,
                        "speed2": 100.0,
                        "targetTime": 0.667
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 10,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.5
                    }
                },
                "super8": {
                    "feeder": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 0,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    },
                    "filmdrive": {
                        "faultTreshold": 16000,
                        "ignoreInitial": 950,
                        "speed": 9000.0,
                        "speed2": 80.0,
                        "targetTime": 0.33
                    },
                    "pickup": {
                        "faultTreshold": 8000,
                        "ignoreInitial": 0,
                        "speed": 800.0,
                        "speed2": 100.0,
                        "targetTime": 0.33
                    }
                }
            },
            "filmdrive": {
                "minSpeed": 20,
                "maxSpeed": 20000,
                "invert": False,
                "learnPin": 19,
                "name": "filmdrive",
                "pinDirection": 14,
                "pinEnable": 18,
                "pinStep": 15,
                "slowEnd": True,
                "stopPin": 26,
                "stopState": 1
            },
            "lights": {
                "blue": 22,
                "green": 27,
                "red": 17
            },
            "pickup": {
                "invert": False,
                "maxSpeed": 20000,
                "minSpeed": 20,
                "name": "pickup",
                "pinDirection": 8,
                "pinEnable": 21,
                "pinStep": 7,
                "slowEnd": False,
                "stopPin": 13,
                "stopState": 1
            }
        }
