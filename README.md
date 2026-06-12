# OpenRidingController
A horse riding game controller for the PC/Mac. The idea is to emulate basic horse riding behaviors and converts those to work a variety of video games.

The controller mainly uses **RP2040 Zero**, **TCRT5000** IR modules and 3D printed parts. Code uses **[CircuitPython 10](https://circuitpython.org/board/waveshare_rp2040_zero/)** for fast prototyping, later revisions may move to Arduino C or something similar.

Currently the controller can emulate keyboard, mouse and DirectInput controller, however, this wont work on any "keyboard to game console" adapter, because of how the USB composite system works.
## Revision 2
Latest revision uses a PCB, and the goal is to minimize the number of 3D printed parts. Strirrups uses an IMU sensors, so controller can be adapted to different frames easily.

<img width="1280" alt="OpenRidingController rev.2" src="https://github.com/user-attachments/assets/84d36122-f2f4-45a9-b111-d2c44c6b3fa4" />

Build guide and BOM in the works.

## Revision 1
Handwired design, frame, sensors etc uses many 3D printed parts. Not in active develoment. 

<img width="1280"  alt="OpenRidingController rev.1" src="https://github.com/user-attachments/assets/75da6f77-70de-4591-b435-3efd1ffd7ecb" />

## Video
[![Video about the project](http://img.youtube.com/vi/zyoOwf0pp80/0.jpg)](http://www.youtube.com/watch?v=zyoOwf0pp80 "OpenRidingController")

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

