#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import datetime
import serial
import thread
#import threading

LOCK = thread.allocate_lock()  # all commands mutex
VLOCK = thread.allocate_lock() # videoproj mutex
BOUNCE = 1000

RED   = 10
GREEN = 9

gpio_button = {23:"ON",    18:"OFF",
               22:"HDMI1", 24:"HDMI2",
               17:"VGA1",  27:"VGA2",
                4:"SDI"}

name_command = {"ON"   : ["VIDEOPROJ", "00!"],
                "OFF"  : ["VIDEOPROJ", "00\""],
                "HDMI1": ["KRAMER",    "#y 0,120,13"],
                "HDMI2": ["KRAMER",    "#y 0,120,14"],
                "VGA1" : ["KRAMER",    "#y 0,120,11"],
                "VGA2" : ["KRAMER",    "#y 0,120,12"],
                "SDI"  : ["KRAMER",    "#y 0,120,17"]
                }

ports = {}
ports["KRAMER"] = serial.Serial(
    port='/dev/serial/by-path/platform-bcm2708_usb-usb-0:1.3:1.0-port0',
#    port='/dev/ttyUSB1',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False,
    timeout = 2,
    writeTimeout = 2
    )

ports["VIDEOPROJ"] = serial.Serial(
    port='/dev/serial/by-path/platform-bcm2708_usb-usb-0:1.2:1.0-port0',
#    port='/dev/ttyUSB0',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False,
    timeout = 2,
    writeTimeout = 2
    )

queue = []

GPIO.setmode(GPIO.BCM)

def led_red():
    GPIO.output(RED, True)
    GPIO.output(GREEN, False)

def led_green():
    GPIO.output(RED, False)
    GPIO.output(GREEN, True)

def led_orange():
    GPIO.output(RED, True)
    GPIO.output(GREEN, True)

def led_black():
    GPIO.output(RED, False)
    GPIO.output(GREEN, False)

def led(l):
    if (l == "G"):
        led_green()
    else:
        if (l == "R"):
            led_red()
        else:
            led_black()

def cmd_failed():
    for i in range(0, 10):
        if (i % 2):
            led_black()
        else:
            led_red()
        time.sleep(0.2)


def videoproj_change_state(cmd, l, t):
    led(l)
    print("Checking VIDEOPROJ powering status")
    rep = send_command("VIDEOPROJ", "00vPK").strip()
    if (rep == "00vPK0"):
        print("Cannot change VIDEOPROJ status now")
        cmd_failed()
        check_videoproj()
        VLOCK.release()
        return

    rep = send_command("VIDEOPROJ", cmd).strip()
    if (rep != cmd):
        print("Command failed")
        cmd_failed()
        check_videoproj()
        VLOCK.release()
        return
        
    for i in range(0, t):
        if (i % 2):
            led(l)
            print l
        else:
            led_black()
            print "."
        time.sleep(1)
    print "Done!"
    led(l)
    VLOCK.release()

def videoproj_on(cmd):
    print "starting videoproj, 60 sec please"
    videoproj_change_state(cmd, "G", 60)

def videoproj_off(cmd):
    print "stopping videoproj, 120 sec please"
    videoproj_change_state(cmd, "R", 120)

def send_command(dev, cmd):
    ser = ports[dev]
    try:
        ser.open()
    except Exception, e:
        print "error open serial port: " + str(e)

    if ser.isOpen():
        try:
            ser.flushInput()
            ser.flushOutput()
            print "SERIAL: sending " + cmd + " to " + dev
            ser.write(cmd + "\r")
            print "SERIAL: sent"
            time.sleep(0.1)
            print "SERIAL: reading answer..."
            response = ser.readline()
            print("SERIAL: read data: " + response)
            ser.close()
            return (response)
        except Exception, e1:
            print "error communicating...: " + str(e1)
    else:
        print "cannot open serial port " + ser.port

def my_callback(channel):
    global gpio_button, name_command, ports, LOCK

    if (LOCK.acquire(0) == False):
        print "bounce!"
        return

    btn_name = gpio_button[channel]
    btn_device = name_command[btn_name][0]
    btn_cmd = name_command[btn_name][1]
    print "event on channel " + str(channel)
    print "button name  : " + btn_name
    print "sending '" + btn_cmd + "' to '" + btn_device + "'"
    queue.append({"dev": btn_device, "cmd": btn_cmd, "btn": btn_name})
    LOCK.release()

def check_videoproj():
    led_orange()
    print("Checking VIDEOPROJ status")
    rep = send_command("VIDEOPROJ", "00vP").strip()
    if (rep == "00vP0"):
        print("VP is OFF --> RED")
        led_red()
    if (rep == "00vP1"):
        print("VP is ON --> GREEN")
        led_green()

GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.output(RED, False)
GPIO.output(GREEN, False)

for k in gpio_button.keys():
    print "setting up button #" + str(k) + " (" +  gpio_button[k] + ")"
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(k, GPIO.FALLING, callback=my_callback, bouncetime=BOUNCE)

try:

    check_videoproj()
#    test = raw_input("Waiting...\n")
#    my_callback(int(test))

    while (True):
        if (len(queue) > 0):
            i = datetime.datetime.now()
            print(i)
            LOCK.acquire(True)
            todo = queue.pop()
            if (todo["dev"] == "VIDEOPROJ"):
                VLOCK.acquire(True)
                if (todo["btn"] == "ON"):
                    videoproj_on(todo["cmd"])
                else:
                    videoproj_off(todo["cmd"])
                check_videoproj()
            else:
                send_command(todo["dev"], todo["cmd"])
            LOCK.release()
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

GPIO.cleanup()

