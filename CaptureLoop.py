
from PyQt5.QtCore import QThread, pyqtSignal
from threading import Thread
import sleep, time
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

class CaptureLoop(QThread):
    signal=pyqtSignal('CaptureLoopStatus')
    def __init__ (self, win):        
        QThread.__init__(self)
        self.win=win
        self.Loop=True

    def run(self):
        # send msgs
        self.signal.emit("Capture loop start")
        
        self.win.motors["feeder"].motor.enable()
        self.win.motors["filmdrive"].motor.enable()
        self.win.motors["pickup"].motor.enable()
        
        self.win.motors["feeder"].motor.clearFault()
        self.win.motors["filmdrive"].motor.clearFault()
        self.win.motors["pickup"].motor.clearFault()
        
        self.win.motors["feeder"].motor.setDirection(self.win.settings["direction"])
        self.win.motors["filmdrive"].motor.setDirection("cw")
        self.win.motors["pickup"].motor.setDirection(self.win.settings["direction"])
        if "saveMode" in self.win.settings and self.win.settings["saveMode"] == "local":
            self.export=LocalThread(self.subDir, self.captureModes[self.win.settings["captureMode"]]["suffix"], self.signal, self.win.settings["localFilePath"])
        else:
            self.export=FtpThread(self.subDir,self.captureModes[self.win.settings["captureMode"]]["suffix"], self.)
        start=self.export.getStartPoint()
        self.export.start()
        self.sequence=FrameSequence(self.cam, self.win.motors, self.win.settings,start,self.uiTools["handleLightChange"])
        
        
        while self.Loop:
            try:
                self.sequence.frameAdvance()
            except Exception as e:
                print(e)
                self.stopLoop()
            if len(listdir('/dev/shm/complete'))>6:
                self.signal.emit("too many files waiting")
                self.signal.emit("pausing up to 5 mins")
                timeout=time()+300
                while (self.Loop and timeout>time() and len(listdir('/dev/shm/complete'))>6):
                    sleep(0.1)
                if timeout <= time():
                    self.signal.emit("timeout xfer error")
                    self.stopLoop()
        self.signal.emit("waiting for files queued for transfer")
        timeout=time()+20
        while len(listdir('/dev/shm/complete'))>0:
            sleep (0.1)
            if time() > timeout:
                self.signal.emit("TIMEOUT waiting for end")
                break
        
        self.win.out.append("stopping Export")
        self.export.stopLoop()        
        self.export.join()
        self.signal.emit("Capture stopped!")


    def stopLoop(self):
        self.signal.emit("Stopping Loop")
        self.Loop=False
    
