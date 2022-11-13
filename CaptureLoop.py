from threading import Thread
from FtpThread import FtpThread
from LocalThread import LocalThread
from time import sleep, time
from json import load,dumps
from os import mkdir,listdir

class FrameSequence():
    def __init__(self, cam, motors, cfg, start_frame,handleLightChange):
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=motors["filmdrive"]
        self.feeder=motors["feeder"]
        self.pickup=motors["pickup"]
        try:
            mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares?");
        self.cam=cam
        self.cam.setFileIndex(start_frame)
        self.handleLightChange=handleLightChange
        self.handleLightChange("on")
        self.feeder.enable()
        self.pickup.enable()
                   
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive)
        m2=MotorThread(self.feeder)
        m3=MotorThread(self.pickup)
        #self.cam.gcApplySettings()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           self.handleLightChange("off")
           raise Exception("Motor Fault!")
        sleep(0.1)
        try:
           self.cam.captureCycle()
        except Exception as e:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           print("Failure to capture image: {}".format(e))
           self.cam.close()
           self.handleLightChange("off")
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
    def __init__ (self, cam, motors, settings, subDir, uiTools):
        Thread.__init__(self)
        self.cam=cam
        self.motors=motors
        self.settings=dict(settings)
        self.subDir=subDir
        self.Loop=True
        self.Pause=False
        self.uiTools=uiTools
        with open("captureModes.json","rt") as h:
            self.captureModes=load(h)
            h.close()

    def run(self):
        self.motors["feeder"].enable()
        self.motors["filmdrive"].enable()
        self.motors["pickup"].enable()
        
        self.motors["feeder"].clearFault()
        self.motors["filmdrive"].clearFault()
        self.motors["pickup"].clearFault()
        
        self.motors["feeder"].setDirection(self.settings["direction"])
        self.motors["filmdrive"].setDirection("cw")
        self.motors["pickup"].setDirection(self.settings["direction"])
        if "saveMode" in self.settings and self.settings["saveMode"] == "local":
            self.export=LocalThread(self.subDir, self.captureModes[self.settings["captureMode"]]["suffix"], self.uiTools, self.settings["localFilePath"])
        else:
            self.export=FtpThread(self.subDir,self.captureModes[self.settings["captureMode"]]["suffix"], self.uiTools)
        start=self.export.getStartPoint()
        self.export.start()
        self.sequence=FrameSequence(self.cam, self.motors, self.settings,start,self.uiTools["handleLightChange"])        
        self.uiTools["runButton"].configure(state="normal",fg="black")
        self.uiTools["prjBox"].configure(state="disable",fg="grey")
        
        while self.Loop:
            try:
                self.sequence.frameAdvance()
            except Exception as e:
                print(e)
                self.stopLoop()
            if len(listdir('/dev/shm/complete'))>6:
                self.uiTools["message"]("too many files waiting")
                self.uiTools["message"]("pausing up to 5 mins")
                timeout=time()+300
                while (self.Loop and timeout>time() and len(listdir('/dev/shm/complete'))>6):
                    sleep(0.1)
                if timeout <= time():
                    self.uiTools["message"]("timeout xfer error")
                    self.stopLoop()
        self.uiTools["message"]("wait end of transfers")
        timeout=time()+20
        while len(listdir('/dev/shm/complete'))>0:
            sleep (0.1)
            if time() > timeout:
                self.uiTools["message"]("TIMEOUT waiting for end")
                break
        
        self.uiTools["message"]("stopping Export")
        self.export.stopLoop()        
        self.export.join()
        self.uiTools["runHandle"].running=False
        self.uiTools["runHandle"].clean=False
        self.uiTools["runButton"].configure(text="Run",state="normal",fg="black")
        self.uiTools["captureModeSelector"].configure(state="normal",fg="black")

        self.uiTools["prjBox"].configure(text="Run",state="normal",fg="black")
        self.uiTools["message"]("Capture stopped!")

    def stopLoop(self):
        self.uiTools["runButton"].configure(state="disabled", fg="grey")
        self.Loop=False
