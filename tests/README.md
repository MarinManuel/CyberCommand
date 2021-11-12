To use the program without a CyberAmp connected to the computer,
you can run `tests/run_fake_cyberamp.sh`

This will create two fake serial port `tests/tty0` to which a fake
CyberAmp is attached. The terminal will output what commands the CyberAmp is
receiving and other debug information.

To use it, connect a serial monitor or the program to `test/tty0`.