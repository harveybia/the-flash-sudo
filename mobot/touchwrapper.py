import RPi.GPIO as GPIO
import time
import os

# PID Control Pre-cast Variables
CTRL_P = 1.8
CTRL_I = 0.0005
CTRL_D = 0.5

# Motor speed configuration
MOTOR_BASESPEED = 255

# --------------------------------------------------------------
# Ramp move constants
# TODO: Trials will determine the parameters to be used on ramp
RAMP_P = 1.5
RAMP_I = 0.0005
RAMP_D = 0.5
RAMP_BASESPEED = 150

RAMP_BTN = 21
GPIO.setmode(GPIO.BCM)

GPIO.setup(RAMP_BTN, GPIO.IN)

class MobotFramework():
    def __init__(self):
        self.incline_btn_prev = False
        self.p = CTRL_P
        self.i = CTRL_I
        self.d = CTRL_D
        self.basespeed = MOTOR_BASESPEED

    def setInclined(self):
        print 'set inclined'
        self.p = RAMP_P
        self.i = RAMP_I
        self.d = RAMP_D
        self.basespeed = RAMP_BASESPEED

    def unsetInclined(self):
        print 'unset inclined'
        self.p = CTRL_P
        self.i = CTRL_I
        self.d = CTRL_D
        self.basespeed = MOTOR_BASESPEED

    def update(self, stop_event=None):
        while True:
            incline_btn = GPIO.input(RAMP_BTN)
            if ((not self.incline_btn_prev) and incline_btn):
                # Button is pressed, set inclined
                self.setInclined()

            elif ((self.incline_btn_prev) and not incline_btn):
                # Button is released, unset inclined
                self.unsetInclined()

            self.incline_btn_prev = incline_btn
            time.sleep(0.05) # This is not to be added in framework.
