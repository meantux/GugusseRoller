from threading import Thread
import RPi.GPIO as GPIO
from time import sleep
from os import nice
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt

GPIO.setmode(GPIO.BCM)



class SensorReport(QThread):
    signal=pyqtSignal("PyQt_PyObject")
    def __init__(self, data, signal):
        QThread.__init__(self)
        self.data=data
        self.signal=signal
        self.previous=[-9, -9, -9, -9]
        self.task=None

    def checkOneInput(self,i):
        actual=GPIO.input(self.data[i][0])
        if actual != self.previous[i]:
            self.previous[i]=actual
            if actual and self.data[i][1]:
                lit=1
            else:
                lit=0
            self.signal.emit(f"{i},{lit}")
                    
    def run(self):
        self.loop=True
        while self.loop:
            i=0
            sleep(0.05)
            while i<4:
                self.checkOneInput(i)
                i+= 1
        self.signal.emit("Out of loop")
                            
    def stopLoop(self):
        print("Stopping sensor loop")
        self.loop=False


class SensorsWidgets(QHBoxLayout):
    signal=pyqtSignal("PyQt_PyObject")
    def __init__(self, win):
        QHBoxLayout.__init__(self)
        self.win=win
        self.startStop=QPushButton("Start Monitoring")
        self.startStop.setCheckable(True)
        self.startStop.toggled.connect(self.handleStartStop)
        self.learn=QPushButton("Learn")
        self.learn.setCheckable(True)
        self.learn.setEnabled(False)
        self.learn.toggled.connect(self.handleLearn)
        self.left=QLabel("L")
        self.hole=QLabel("H")
        self.right=QLabel("R")
        self.addWidget(self.startStop)
        self.addWidget(self.learn)
        
        self.addWidget(self.left)
        self.addWidget(self.hole)
        self.addWidget(self.right)
        self.signal.connect(self.handleSensorChange)
        hw=win.hwSettings
        self.data=[
            (hw["feeder"]["stopPin"], hw["feeder"]["stopState"]),
            (hw["filmdrive"]["stopPin"], hw["filmdrive"]["stopState"]),
            (hw["pickup"]["stopPin"], hw["pickup"]["stopState"]),
            (hw["filmdrive"]["learnPin"], 1)
        ]
        self.setcolors(self.learn, "grey", "grey")
        self.setcolors(self.left, "grey", "grey")
        self.setcolors(self.hole, "grey", "grey")
        self.setcolors(self.right, "grey", "grey")  
        self.left.setAlignment(Qt.AlignCenter)
        self.hole.setAlignment(Qt.AlignCenter)
        self.right.setAlignment(Qt.AlignCenter)
      

    def handleStartStop(self, checked):
        if checked:
            self.setcolors(self.startStop, "lightgreen", "black")
            self.task=SensorReport(self.data, self.signal)
            self.task.start()
            self.enableLearnIfPossible()
        else:
            self.setcolors(self.startStop, "grey", "grey")            
            self.startStop.setEnabled(False)
            self.learn.setEnabled(False)
            self.task.stopLoop()
            self.task=None

    def handleLearn(self, checked):
        pin=self.win.hwSettings["filmdrive"]["learnPin"]
        if checked:
            GPIO.output(pin,1)
            self.setcolors(self.learn, "white", "black")
            
        else:
            GPIO.output(pin,0)
            self.setcolors(self.learn, "black", "white")
                    
    def enableLearnIfPossible(self):
        if self.task == None or self.win.runStop.isCapturing(): 
            return
        self.learn.setEnabled(True)
        
    def setcolors(self, lbl, bg, fg):
        lbl.setStyleSheet(f"""
        background-color: {bg};
        color: {fg};
        """)
    
    def handleSensorChange(self, msg):
        # also known as the signal handler
        if msg == "Out of loop":
            self.startStop.setEnabled(True)
            self.learn.setEnabled(False)
            self.setcolors(self.left, "grey", "grey")
            self.setcolors(self.hole, "grey", "grey")
            self.setcolors(self.right, "grey", "grey")
            self.setcolors(self.learn, "grey", "grey")
            self.setcolors(self.startStop, "lightgrey", "black")            
        else:
            split=msg.split(",")
            if msg == "3,0":
                self.learn.setChecked(False)
            elif msg == "3,1":
                self.learn.setChecked(True)
                
            if split[0] == "0":
                lbl=self.left
            elif split[0] == "1":
                lbl=self.hole
            elif split[0] == "2":
                lbl=self.right
            elif split[0] == "3":
                lbl=self.learn
            if split[1] == "0":
                self.setcolors(lbl, "black", "white")                
            else:
                self.setcolors(lbl, "lightgreen", "black")
        
