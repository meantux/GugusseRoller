# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GugusseRoller is a DIY film scanner controller running on a **Raspberry Pi 4B** (Raspbian Bullseye 64-bit). It drives 3 stepper motors, controls a Raspberry Pi HQ Camera (IMX477), reads GPIO sensors, and transfers captured frames via FTP or local copy.

**This software cannot run on any workstation.** It requires Raspberry Pi hardware: GPIO pins for motor control and sensors, the RPi HQ Camera via libcamera/picamera2, and RPi.GPIO. The development workstation is used only for editing code; all testing must be done on the Pi.

## Running the Applications

```bash
# Main GUI application (requires Raspberry Pi hardware)
python3 GugusseGUI.py

# Setup wizard for motor direction and FTP/local export config
python3 MotorsAndFtpSetup.py

# Standalone RAW viewer / 12-bit CSI2P histogram inspector (works without Pi hardware in simulation mode)
python3 raw_viewer.py

# Control lights from command line
python3 Lights.py <on|off|red|green|blue|cyan|magenta|yellow>
```

There are no automated tests and no build step — all files are run directly.

## Key Dependencies

- **PyQt5** — main GUI framework (used in all UI modules)
- **picamera2** — Raspberry Pi camera interface (wraps libcamera)
- **RPi.GPIO** — GPIO pin control for motors and sensors
- **libcamera** — camera transform and controls enums
- **pyqtgraph** + **numpy** — used only in `raw_viewer.py` for histogram display

All dependencies are Raspberry Pi-specific. Do not attempt to run or test any of these scripts on the workstation.

## Architecture

### Signal/Thread Model

The GUI runs on the Qt main thread. Background work uses `QThread` with `pyqtSignal` for cross-thread communication. The pattern throughout is:
- A `QThread` subclass does blocking hardware I/O
- It emits a `signal` (always typed `"PyQt_PyObject"`) with string messages
- The connected slot on the main thread parses the message and updates the UI

String messages from `CaptureLoop`/`FtpThread` follow ad-hoc protocols:
- `"xfer,<filename>"` → update last-transferred file label
- `"syncMotors"` → refresh motor power-state icons
- `"turning lights off"` → turn off lights
- `"spdchg,<motorname>,<speed>"` → update speedmeter label
- `"Capture stopped!"` → re-enable UI widgets

### Capture Pipeline

1. `CaptureLoop` (QThread) → calls `FrameSequence.frameAdvance()` in a loop
2. `FrameSequence.frameAdvance()` → calls `GCamera.captureCycle()` which writes a file to `/dev/shm/<num>.ext`, then renames it to `/dev/shm/complete/<num>.ext`
3. `FtpThread` or `LocalThread` (Python Thread) → polls `/dev/shm/complete/` every second and transfers/moves files out

The `/dev/shm/complete/` directory acts as a FIFO queue between capture and export. If more than 6 files accumulate, capture pauses for up to 5 minutes.

### Motor Control

`TrinamicSilentMotor` drives Trinamic stepper drivers via 3 GPIO pins each (step, direction, enable). Two motor types have different `move()` implementations:
- **filmdrive** (`isFilmDrive: true`) — counts steps to the hole-detection sensor, uses a "learn pin" to signal the Arduino
- **feeder / pickup** (`isFilmDrive: false`) — times the move to an arm-position sensor

Speed is auto-adjusted each cycle via `calculateNewSpeed()` using a rolling 6-sample history compared to `targetTime`.

### Configuration Files

All config is stored as JSON in the working directory and managed by `ConfigFiles` (subclass of `dict`):
- `GugusseSettings.json` — camera settings (exposure, ISO, white balance, fps, flip)
- `hardwarecfg.json` — GPIO pin assignments, film format parameters per motor, lights pins, save mode
- `ftp.json` — FTP server credentials and path
- `captureModes.json` — capture mode definitions (DNG, singleJpg, bracketing)

`ConfigFiles` auto-creates files with defaults on first run. Saves atomically via a temp file + `shutil.move`.

### UI Layout (GugusseGUI.py)

`MainWindow` assembles all widget modules:
- Row 1: Exposure mode, exposure slider, ISO
- Row 2: White balance mode, freeze WB, red/blue gain
- Row 3: Brightness, contrast, sharpness, saturation
- Bottom left: flip checkboxes, save settings; 3 motor widgets (feeder/filmdrive/pickup with CW/CCW manual buttons); lights selector, project name, film format, capture mode, reels direction, snapshot/run-stop buttons, sensor monitoring
- Bottom right: live camera preview (`QGlPicamera2`), click to zoom/unzoom

### Widget Pattern

Most UI controls follow a consistent pattern:
- Subclass a Qt widget (QSlider, QComboBox, QPushButton, etc.)
- Store a companion `QLabel` returned by `getLabel()`, inserted separately into layouts
- Implement `syncCamera()` to push current state to `picam2.set_controls()`
- Read/write from `win.settings` (the `ConfigFiles` dict) for persistence

### raw_viewer.py (histogram2 branch)

Standalone tool for exploring 12-bit CSI2P raw data from the IMX477. Uses `pyqtgraph` for fast histogram rendering. Implements 8 different 12-bit unpacking modes for debugging raw pixel data interpretation. Must run on the Pi like everything else.
