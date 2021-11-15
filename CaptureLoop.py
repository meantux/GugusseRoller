from threading import Thread
from FtpThread import FtpThread


from TrinamicSilentMotor import TrinamicSilentMotor
from time import sleep, time
from Lights import Lights
import os
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

class Gugusse():
    def __init__(self, cfg, start_frame):
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
        self.cam=GCamera(start_frame)
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


class MotorThread (threading.Thread):
   def __init__(self, motor):
      threading.Thread.__init__(self)
      self.motor=motor
   def run(self):
      self.motor.move()



class CaptureLoop(Thread):
    def __init__ (self, settings, subDir):
        Thread.__init__(self)
        self.settings=settings
        self.subDir=subDir
        self.Loop=True
        with open("filmFormats.json","rt") as h:
            filmformats=load(h)
        with open("hardwarecfg.json","rt") as h:
            self.hardware=load(h)
        for device in filmformats:
            self.hardware[device].update(filmformats[device])
        
        

    def run(self):
        
        
    def stopLoop(self):
        self.Loop=False
    
        
