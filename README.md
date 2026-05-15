# OpenRidingController

A horse riding game controller for the PC/Mac. The idea is to emulate basic horse riding behaviors and converts those to work a variety of video games.

The controller mainly uses **RP2040 Zero**, **TCRT5000** IR modules and 3D printed parts. Code uses **[CircuitPython 10](https://circuitpython.org/board/waveshare_rp2040_zero/)** for fast prototyping, later revisions may move to Arduino C or something similar.

Currently the controller can emulate keyboard, mouse and DirectInput controller, however, this wont work on any "keyboard to game console" adapter, because of how the USB composite system works.

## Hardware Required

 - RP2040 Zero
 - 4 pcs TCRT5000 Infrared Reflective Sensor (with analog out)
 - [3D Printed parts, steel pipes and M3 hardware](https://github.com/Squalius-cephalus/OpenRidingController/tree/main/3D_files)

## Required Libraries

 - [Adafruit CircuitPython HID Library](https://github.com/adafruit/Adafruit_CircuitPython_HID/tree/main)
 - [Adafruit CircuitPython Nunchuk](https://github.com/adafruit/Adafruit_CircuitPython_Nunchuk)
 - Adafruit Neopixel
 - Bus Devices
 - Simple Math

## Circuit Diagram
<img width="1500" height="749" alt="circuit_diagram" src="https://github.com/user-attachments/assets/bce18d3e-5612-4eaf-a589-6673e27abf7a" />



**TODO:** 
Add pictures
Add guide how to use
