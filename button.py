#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import serial
import thread
from daemon import runner

class App():
    LOCK = thread.allocate_lock()
    BOUNCE = 1000

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
    
    queue = []

    def send_command(dev, cmd):
        ser = self.ports[dev]
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
        print "callback!"
        if (self.LOCK.acquire(0) == False):
            print "bounce!"
            return
        btn_name = self.gpio_button[channel]
        btn_device = self.name_command[btn_name][0]
        btn_cmd = self.name_command[btn_name][1]
        print "event on channel " + str(channel)
        print "button name  : " + btn_name
        print "sending '" + btn_cmd + "' to '" + btn_device + "'"
        self.queue.append({"dev": btn_device, "cmd": btn_cmd})
        self.LOCK.release()

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/var/log/button.err'
        self.pidfile_path =  '/tmp/button.pid'
        self.pidfile_timeout = 5

    def run(self):
        for k in self.gpio_button.keys():
            print "setting up button #" + str(k) + " (" +  self.gpio_button[k] + ")"
            GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(k, GPIO.FALLING, callback=self.my_callback, bouncetime=self.BOUNCE)

        try:
            while (True):
#                test = raw_input("Waiting...\n")
#                my_callback(int(test))
                if (len(self.queue) > 0):
                    self.LOCK.acquire(True)
                    todo = self.queue.pop()
                    self.LOCK.release()
                    self.send_command(todo["dev"], todo["cmd"])
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

        GPIO.cleanup()

app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
