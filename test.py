#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import serial

ser = serial.Serial("/dev/ttyUSB1", 9600, timeout=5) # videoproj
#ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=5) # kramer

ser.setDTR(level = True)
ser.setRTS(level = True)

# ser.write("#y 0,120,11,0\n")
ser.write("00vLST\r")
print "sent"
response = ser.readline()
if response:
    print("read data: " + response)
