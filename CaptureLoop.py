from threading import Thread
from FtpThread import FtpThread

from TrinamicSilentMotor import TrinamicSilentMotor
from time import sleep, time
from Lights import Lights
from json import load,dumps
import os
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

class FrameSequence():
    def __init__(self, cam, cfg, start_frame):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=TrinamicSilentMotor(cfg["filmdrive"], trace=True)
        self.feeder=TrinamicSilentMotor(cfg["feeder"],autoSpeed=True)
        self.pickup=TrinamicSilentMotor(cfg["pickup"],autoSpeed=True)
        try:
            os.mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares?");
        self.feeder.enable()
        self.filmdrive.enable()
        self.pickup.enable()
        self.cam=cam
        self.cam.setFileIndex(start_frame)
        self.lights=Lights("on")
                   
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive)
        m2=MotorThread(self.feeder)
        m3=MotorThread(self.pickup)
        #self.cam.gcApplySettings()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           self.lights.set("off")
           raise Exception("Motor Fault!")
        sleep(0.05)
        try:
           self.cam.captureCycle()
        except Exception as e:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           print("Failure to capture image: {}".format(e))
           self.cam.close()
           self.lights.set("off")
           raise Exception("Stop")
        m2.start()
        m3.start()
        m3.join()
        m2.join()
        m1.start()
        m1.join()

class MotorThread (Thread):
   def __init__(self, motor):
      Thread.__init__(self)
      self.motor=motor
   def run(self):
      self.motor.move()

class CaptureLoop(Thread):
    def __init__ (self, cam, settings, subDir, uiTools):
        Thread.__init__(self)
        self.cam=cam
        self.settings=dict(settings)
        self.subDir=subDir
        self.Loop=True
        self.Pause=False
        self.uiTools=uiTools
        with open("filmFormats.json","rt") as h:
            filmformats=load(h)
            h.close()
        with open("hardwarecfg.json","rt") as h:
            self.hardware=load(h)
            h.close()
        with open("captureModes.json","rt") as h:
            self.captureModes=load(h)
            h.close()
        print("filmformats={}".format(dumps(filmformats[settings["filmFormat"]],indent=4)))
        print("hardware={}".format(dumps(self.hardware,indent=4)))
        chosenOne=filmformats[settings["filmFormat"]]
        for device in chosenOne:
            self.hardware[device].update(chosenOne[device])
        print("merge={}".format(dumps(self.hardware,indent=4)))
        if settings["direction"] == "cw":
            self.hardware["feeder"]["invert"]=not self.hardware["feeder"]["invert"]
            self.hardware["pickup"]["invert"]=not self.hardware["pickup"]["invert"]
        for anything in self.hardware:
            self.settings[anything]=self.hardware[anything]

    def run(self):
        self.uiTools["runButton"].configure(state="disabled",fg="grey")
        self.ftp=FtpThread(self.subDir,self.captureModes[self.settings["captureMode"]]["suffix"])
        start=self.ftp.getStartPoint()
        self.ftp.start()
        self.sequence=FrameSequence(self.cam, self.settings, start)        
        self.uiTools["runButton"].configure(state="normal",fg="black")
        while self.Loop:
            try:
                self.sequence.frameAdvance()
            except Exception as e:
                print(e)
                self.stopLoop()
        print("Giving a change to background FTP to finish")
        sleep(10)
        print("stopping FTP background")
        self.ftp.stopLoop()
        self.ftp.join()
        self.uiTools["runHandle"].running=False
        self.uiTools["message"].configure(text="stopped running")
        self.uiTools["runButton"].configure(state="normal",fg="black")

    def stopLoop(self):
        self.uiTools["runButton"].configure(state="disabled", fg="grey")
        self.Loop=False
