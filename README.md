# CyberCommand
Python implementation of the Axon Inst. Cyberclamp CyberControl software

The CyberAmp 380 is (was?) a comprehensive computer-controlled eight-channel instrument suitable for almost all forms of laboratory signal amplification, filtering, and transduction.
![Picture of a CyberAmp 380](https://user-images.githubusercontent.com/65401298/141604688-629ca995-776c-426f-9f12-c1614ef490fe.png)

Unfortunately, the software used to control the amplifier Axon Inst. CyberControl has been lost to time, and most likely is incompatible with newer versions of windows. Fortunately, the amplifier is controlled using serial commands, and the protocol is extremely well documented in the manual.

This is a reimplementation of the CyberControl software in Python.
![Screenshot of the main interface](https://user-images.githubusercontent.com/65401298/141604881-bbbf2747-377f-4608-9d3d-a269e2176483.png)

## requirements
- pyserial
- PyQt5
