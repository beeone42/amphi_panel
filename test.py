#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import serial

ser = serial.Serial("/dev/ttyUSB1", 9600, timeout=1)

ser.setDTR(level = True)
ser.setRTS(level = True)

#    ser.write("#y 0,120,11\n")
ser.write("00!\n")
print "sent"
response = ser.read(4)
if response:
    print("read data: " + response)
