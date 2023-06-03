from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QPushButton
from threading import Thread
from time import sleep, time
from json import load,dumps
from os import mkdir,listdir
from FtpThread import FtpThread
from LocalThread import LocalThread


class FrameSequence():
    def __init__(self, win, start_frame, signal):
        self.win=win
        self.signal=signal
        self.filmdrive=self.win.motors["filmdrive"].motor
        self.feeder=self.win.motors["feeder"].motor
        self.pickup=self.win.motors["pickup"].motor
        try:
            mkdir("/dev/shm/complete")
        except Exception as e:
            self.signal.emit(str(e))
            self.signal.emit("Ho well... directory already exists, who cares?");
        self.cam=self.win.picam2
        self.cam.setFileIndex(start_frame)
        self.win.light_selector.signal.emit("on")
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
           self.win.light_selector.signal.emit("off")
           self.signal.emit("---------------------------------------------")
           self.signal.emit("\"Motor faults\" are issues with the sequence")
           self.signal.emit("they could be triggered by obvious reasons")
           self.signal.emit("like film's end or a film break.")
           self.signal.emit("Or less obvious reasons like film stuck, film")
           self.signal.emit("loose, film missing static friction, too much")
           self.signal.emit("friction by under lubrified bearings, tape")
           self.signal.emit("over film holes, hole sensor misaligned, film")
           self.signal.emit("out of specs, lightpipes displaced, blocked")
           self.signal.emit("sensors, wire disconnected...")
           self.signal.emit("---------------------------------------------")
           raise Exception("Capture stopped by Motor Faults!")
        sleep(0.1)
        try:
           self.cam.captureCycle()
        except Exception as e:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           self.signal.emit("Failure to capture image: {}".format(e))
           self.win.light_selector.signal.emit("off")
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
    def __init__ (self, win, signal):        
        QThread.__init__(self)
        self.signal=signal
        self.win=win
        self.Loop=True
        with open("captureModes.json", "rt") as h:
            self.captureModes=load(h)

    def run(self):
        # send msgs
        self.signal.emit("Capture loop start")
        currentFilmFormatCfg=self.win.hwSettings["filmFormats"][self.win.filmFormat.currentText()]
        self.signal.emit(dumps(currentFilmFormatCfg, indent=4))
        self.win.motors["feeder"].motor.setFormat(currentFilmFormatCfg["feeder"])
        self.win.motors["filmdrive"].motor.setFormat(currentFilmFormatCfg["filmdrive"])
        self.win.motors["pickup"].motor.setFormat(currentFilmFormatCfg["pickup"])

        self.win.motors["feeder"].motor.enable()
        self.win.motors["filmdrive"].motor.enable()
        self.win.motors["pickup"].motor.enable()
        
        self.win.motors["feeder"].motor.clearFault()
        self.win.motors["filmdrive"].motor.clearFault()
        self.win.motors["pickup"].motor.clearFault()
        
        self.win.motors["feeder"].motor.setDirection(self.win.reelsDirection.currentText())
        self.win.motors["filmdrive"].motor.setDirection("cw")
        self.win.motors["pickup"].motor.setDirection(self.win.reelsDirection.currentText())
        
        if "saveMode" in self.win.hwSettings and self.win.hwSettings["saveMode"] == "local":
            self.export=LocalThread(self.win.projectName.text(), self.captureModes[self.win.captureMode.currentText()]["suffix"], self.signal, self.win.hwSettings["localFilePath"])
        else:
            self.export=FtpThread(self.win.projectName.text(),self.captureModes[self.win.captureMode.currentText()]["suffix"], self.signal)
        start=self.export.getStartPoint()
        self.export.start()
        self.sequence=FrameSequence(self.win,start, self.signal)
                
        while self.Loop:
            try:
                self.sequence.frameAdvance()
            except Exception as e:
                self.signal.emit(str(e))
                self.stopLoop()
            if len(listdir('/dev/shm/complete'))>6:
                self.signal.emit("too many files waiting")
                self.signal.emit("waiting up to 5 mins")
                timeout=time()+300
                while (self.Loop and timeout>time() and len(listdir('/dev/shm/complete'))>6):
                    sleep(0.1)
                if timeout <= time():
                    self.signal.emit("timeout xfer error")
                    self.stopLoop()
        self.signal.emit("waiting up to 2 minutes for transfer queue to be cleared")
        timeout=time()+120
        while len(listdir('/dev/shm/complete'))>0:
            sleep (0.1)
            if time() > timeout:
                self.signal.emit("TIMEOUT waiting for end")
                break
        
        self.signal.emit("stopping Export")
        self.export.stopLoop()        
        self.export.join()
        self.signal.emit("Capture stopped!")


    def stopLoop(self):
        self.signal.emit("Stopping Loop")
        self.Loop=False
    

class RunStopWidget(QPushButton):
    signal=pyqtSignal("PyQt_PyObject")
    def __init__(self, win):
        QPushButton.__init__(self, "Run")
        self.win=win        
        self.clicked.connect(self.handlePush)
        self.signal.connect(self.handleSignal)
        self.running=False
        self.stopping=False

    def captureWidgetsEnable(self, state):
        self.win.filmFormat.setEnabled(state)
        self.win.projectName.setEnabled(state)
        self.win.captureMode.setEnabled(state)
        self.win.light_selector.setEnabled(state)

    def handlePush(self):
        if not self.running:
            self.captureWidgetsEnable(False)
            self.running=True
            self.run=CaptureLoop(self.win, self.signal)
            self.run.start()
            self.setText("Stop")
        else:
            self.setEnabled(False)
            self.setText("Stopping!")
            self.stopping=True
            self.run.stopLoop()
            
    def isCapturing(self):
        return self.running

    def warnReelChange(self,direction):
        if self.running:
            self.win.motors["feeder"].motor.setDirection(direction)
            self.win.motors["pickup"].motor.setDirection(direction)
            self.win.out.append(f"Changing reels directions live to {direction}")
    
    def handleSignal(self, unfiltered):
        msg=str(unfiltered)
        self.win.out.append(msg)
        if msg=="Capture stopped!":
            self.setText("Run")
            self.captureWidgetsEnable(True)
            self.win.light_selector.handleSignal("off")
            self.running=False
            self.setEnabled(True)
        if msg=="Stopping Loop":
            self.setEnabled(False)
            self.setText("Stopping")
        

class SnapshotWidget(QPushButton):
    def __init__(self, win):
        QPushButton.__init__(self)
        self.win=win
        self.setIcon(QIcon('camera.png'))
        self.clicked.connect(self.handle)
        

    def handle(self):
        self.win.out.append("Not implemented yet")

