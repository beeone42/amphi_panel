#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
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
    port='/dev/ttyUSB1',
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
    port='/dev/ttyUSB0',
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

def videoproj_on():
    print "starting videoproj, 60 sec please"
    GPIO.output(RED, False)
    for i in range(0, 60):
        if (i % 2):
            GPIO.output(GREEN, True)
            print "G"
        else:
            GPIO.output(GREEN, False)
            print "."
        time.sleep(1)
    print "Done!"
    GPIO.output(GREEN, True)
    VLOCK.release()

def videoproj_off():
    print "stopping videoproj, 120 sec please"
    GPIO.output(GREEN, False)
    for i in range(0, 120):
        if (i % 2):
            GPIO.output(RED, True)
            print "R"
        else:
            GPIO.output(RED, False)
            print "."
        time.sleep(1)
    print "Done!"
    GPIO.output(RED, True)
    VLOCK.release()

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
            print "sending " + cmd + " to " + dev
            ser.write(cmd + "\r")
            print "sent"
            time.sleep(0.1)
            print "reading answer..."
            response = ser.readline()
            print("read data: " + response)
            ser.close()
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

GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.output(RED, False)
GPIO.output(GREEN, False)


for k in gpio_button.keys():
    print "setting up button #" + str(k) + " (" +  gpio_button[k] + ")"
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(k, GPIO.FALLING, callback=my_callback, bouncetime=BOUNCE)

try:
    test = raw_input("Waiting...\n")
    my_callback(int(test))
    while (True):
        if (len(queue) > 0):
            LOCK.acquire(True)
            todo = queue.pop()
            if (todo["dev"] == "VIDEOPROJ"):
                VLOCK.acquire(True)
                send_command(todo["dev"], todo["cmd"])
                if (todo["btn"] == "ON"):
                    videoproj_on()
                    #w = threading.Thread(target=videoproj_on)
                else:
                    videoproj_off()
                    #w = threading.Thread(target=videoproj_off)
                #w.start()
            else:
                send_command(todo["dev"], todo["cmd"])
            LOCK.release()
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

GPIO.cleanup()

