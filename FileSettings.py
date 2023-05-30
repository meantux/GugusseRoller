from PyQt5.QtWidgets import QComboBox, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from datetime import datetime
import json
import re

import re

def makeValidFilename(input_str):
    s = input_str.replace(' ', '_')
    s = re.sub(r'[^\w\-_]', '', s)
    s = s.encode("ascii", "ignore").decode()
    return s



class ProjectNameWidget(QLineEdit):
    def __init__(self, win):
        QLineEdit.__init__(self)
        self.win=win
        self.label=QLabel("Project")
        self.label.setAlignment(Qt.AlignRight)
        self.setText(datetime.now().strftime("%Y%m%d-%H%M"))
        self.editingFinished.connect(self.handle)

    def handle(self):
        text=self.text()
        valid=makeValidFilename(text)
        if valid != text:
            self.setText(valid)
        
    def getLabel(self):
        return self.label


class FilmFormatWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        self.win=win
        self.label=QLabel("Format")
        self.label.setAlignment(Qt.AlignRight)
        self.allFormats=self.win.hwSettings["filmFormats"]
        self.addItems(self.allFormats.keys())
        if "FilmFormat" not in self.win.settings or self.win.settings["FilmFormat"] not in self.allFormats:
            current=list(self.allFormats.keys())[0]
        else:
            current=self.win.settings["FilmFormat"]
        self.setCurrentText(current)
        self.currentTextChanged.connect(self.handle)

    def handle(self, text):
        self.win.out.append(f"film format changed to {text}")

    def getLabel(self):
        return self.label

class CaptureModeWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        with open("captureModes.json", "rt") as h:
            self.modes=json.load(h)            
        self.win=win        
        self.label=QLabel("Output")
        self.label.setAlignment(Qt.AlignRight)
        self.addItems(self.modes.keys())
        if "CaptureMode" not in self.win.settings or self.win.settings["CaptureMode"] not in self.modes:
            current=list(self.modes.keys())[0]
        else:
            current=self.win.settings["CaptureMode"]
        self.setCurrentText(current)
        self.currentTextChanged.connect(self.handle)

    def handle(self, text):
        self.win.out.append(f"Capture Mode changed to {text}")

    def currentMode():
        return self.modes[self.currentText()]

    def getLabel(self):
        return self.label
