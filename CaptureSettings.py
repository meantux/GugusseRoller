from PyQt5.QtWidgets import QComboBox, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from datetime import datetime
import json
import re
import os


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
        self.win.settings["FilmFormat"]=text

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
        self.win.settings["CaptureMode"]=text

    def currentMode():
        return self.modes[self.currentText()]

    def getLabel(self):
        return self.label

class ReelsDirectionWidget(QComboBox):
    def __init__(self, win):
        QComboBox.__init__(self)
        choices=["cw","ccw"]
        self.win=win
        self.label=QLabel("Reels Direction")
        self.label.setAlignment(Qt.AlignRight)
        self.addItems(choices)        
        if "ReelsDirection" in self.win.settings:
            setting=self.win.settings["ReelsDirection"]
        else:
            setting="cw"
            self.win.settings["ReelsDirection"]=setting

        if setting in choices:
            self.setCurrentText(setting)
        else:
            self.setCurrentText("cw")
            self.win.settings["ReelsDirection"]="cw"
        self.currentTextChanged.connect(self.handle)

    def handle(self, text):
        self.win.settings["ReelsDirection"]=text

    def getLabel(self):
        return self.label

class SaveSettingsWidget(QPushButton):
    def __init__(self, win):
        QPushButton.__init__(self, "Save Settings")
        self.clicked.connect(self.execute)
        self.win=win
        self.lastSaved=dict(self.win.settings)

    def thereAreUnsavedSettings(self):
        return self.lastSaved!=self.win.settings

    def execute(self):
        if not self.thereAreUnsavedSettings():
            self.win.out.append("Nothing to save.")
            return
        h=open(".buildingJson", "wt")
        json.dump(self.win.settings, h, indent=4)
        h.close()
        os.rename(".buildingJson", "GugusseSettings.json")
        self.lastSaved=dict(self.win.settings)
        self.win.out.append("Settings saved.")
