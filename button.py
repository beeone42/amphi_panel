#!/usr/bin/env python

import RPi.GPIO as GPIO

BOUNCE=500

gpio_buttonid = {18:1, 23:2, 24:3, 4:4, 17:5, 21:6, 22:7}
buttonid_name = {1:"OFF", 2:"ON", 3:"HDMI2", 4:"HDMI1", 5:"VGA2", 6:"VGA1", 7:"SDI"}


GPIO.setmode(GPIO.BCM)

def my_callback(channel):
    global gpio_buttonid, buttonid_name
    print "event on channel " + str(channel)
    print "button number: " + str(gpio_buttonid[channel])
    print "button name  : " + buttonid_name[gpio_buttonid[channel]]

for k in gpio_buttonid.keys():
    print "setting up button #" + str(k) + " (" +  str(gpio_buttonid[k]) + ":" + buttonid_name[gpio_buttonid[k]] + ")"
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(k, GPIO.FALLING, callback=my_callback, bouncetime=BOUNCE)

try:
    raw_input("Waiting...\n")
except KeyboardInterrupt:
    pass

GPIO.cleanup()

