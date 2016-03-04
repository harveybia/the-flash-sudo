# Copyright 2016 Harvey Shi
# This module includes controls for BrickPi, specifically designed for
# project the-flash.

# Hardware Configurations:
# Raspberry Pi 2 x1
# BrickPi x1
# EV3 Touch Sensor x1 - Port: S2
# EV3 Motors x2 - Left: B; Right: C

from BrickPi import *
import threading
import time

# Reference: BrickPi_Python/Sensor_Examples/*.py
# Setup serial port for communications
BrickPiSetup()

# Aliasing for ports for convenience
L = PORT_B
R = PORT_C
S2 = PORT_2

# Exceptions
class ParameterInvalidException(Exception):
    def __init__(self, description):
        self.des = description

    def __str__(self):
        return repr(self.des)

# Left and Right Sensors:
BrickPi.MotorEnable[L] # LEFT
BrickPi.MotorEnable[R] # RIGHT

# Touch Sensor Initialization:
BrickPi.SensorType[S2] = TYPE_SENSOR_EV3_TOUCH_DEBOUNCE

# Send properties of sensors to BrickPi
BrickPiSetupSensors()

class Controller:
    def __init__(self):
        self.touchcallback = None
        self.touchcount = 0
        self.encL = 0
        self.encR = 0

    def update(self):
        self.touchcount = abs(self.touchcount - 1)
        result = BrickPiUpdateValues()
        if not result:
            # Successfully updated values
            if BrickPi.Sensor[S2]:
                # This algorithm is used to prevent misinterpretation
                self.touchcount += 2
                if self.touchcount > 20:
                    if self.touchcallback: self.touchcallback()
            # Update Encoder Values
            self.encL = BrickPi.Encoder[L]
            self.encR = BrickPi.Encoder[R]
        time.sleep(0.01)

    def setMotorSpeed(self, l, r):
        if abs(l) > 255 or abs(r) > 255:
            raise ParameterInvalidException("Invalid motor speeds")
        BrickPi.MotorSpeed[L] = l
        BrickPi.MotorSpeed[R] = r

    def setTouchCallback(self, func):
        self.touchcallback = func

    def getEncoderValues(self):
        # getEncoderValues() -> tuple (x, y)
        return (self.encL, self.encR)

if __name__ == "__main__":
    # Unit Test
    def mainloop(c):
        while 1:
            c.update()

    def isTouched():
        print "S2 Activated"

    con = Controller()
    con.setTouchCallback(isTouched)
    thd = threading.Thread(target=mainloop, args=(con,), daemon=True)
    thd.start()

    print "Started Controller Instance"
    time.sleep(0.5)
    print "Testing Motors:"
    con.setMotorSpeed(100, 100)
    time.sleep(2)
    con.setMotorSpeed(-100, -100)
    time.sleep(2)

    print "Testing Sensors:"
    print "<Press S2 to test callback, strike enter to quit>"
    rawinput()
