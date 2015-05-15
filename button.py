#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import serial

LOCK=False
BOUNCE=1000

#gpio_buttonid = {18:1, 23:2, 24:3, 4:4, 17:5, 21:6, 22:7}
#buttonid_name = {1:"OFF", 2:"ON", 3:"HDMI2", 4:"HDMI1", 5:"VGA2", 6:"VGA1", 7:"SDI"}

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
    port='/dev/ttyUSB0',
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
    port='/dev/ttyUSB1',
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


GPIO.setmode(GPIO.BCM)

def send_command(ser, cmd):
    try:
        print "Opening serial port " + ser.port
        ser.open()
    except Exception, e:
        print "error open serial port: " + str(e)

    if ser.isOpen():
        try:
            ser.flushInput()
            ser.flushOutput()
            print "sending data..."
            ser.write(cmd + "\n")
            print "sent"
            time.sleep(0.1)
            print "reading answer..."
            response = ser.readline()
            print("read data: " + response)
            ser.close()
        except Exception, e1:
            print "error communicating...: " + str(e1)
    else:
        print "cannot open serial port "

def my_callback(channel):
    global gpio_button, name_command, ports, LOCK


    if (LOCK):
        print "bounce!"
        return
    LOCK=True

#    btn_id = gpio_buttonid[channel]
#    btn_name = buttonid_name[btn_id]

    btn_name = gpio_button[channel]
    btn_device = name_command[btn_name][0]
    btn_cmd = name_command[btn_name][1]
    print "event on channel " + str(channel)
#    print "button number: " + str(btn_id)
    print "button name  : " + btn_name
    print "sending '" + btn_cmd + "' to '" + btn_device + "'"
    send_command(ports[btn_device], btn_cmd)
    LOCK=False

for k in gpio_button.keys():
    print "setting up button #" + str(k) + " (" +  gpio_button[k] + ")"
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(k, GPIO.FALLING, callback=my_callback, bouncetime=BOUNCE)

try:
    test = raw_input("Waiting...\n")
    my_callback(int(test))

except KeyboardInterrupt:
    pass

GPIO.cleanup()

