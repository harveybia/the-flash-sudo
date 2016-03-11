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
S2 = PORT_4

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
        self.vL = 0
        self.vR = 0
        self.encL = 0
        self.encR = 0

    def update(self):
        self.touchcount = abs(self.touchcount - 1)
        BrickPi.MotorSpeed[L] = self.vL
        BrickPi.MotorSpeed[R] = self.vR
        result = BrickPiUpdateValues()
        if not result:
            # Successfully updated values
            if BrickPi.Sensor[S2]:
                # This algorithm is used to prevent misinterpretation
                self.touchcount += 2
                if self.touchcount > 8:
                    if self.touchcallback:
                        self.touchcallback()
                    self.touchcount = 0
            # Update Encoder Values
            self.encL = BrickPi.Encoder[L]
            self.encR = BrickPi.Encoder[R]
        time.sleep(0.01)

    def setMotorSpeed(self, l, r):
        if abs(l) > 255 or abs(r) > 255:
            raise ParameterInvalidException("Invalid motor speeds")
        self.vL = l; self.vR = r
        # BrickPi.MotorSpeed[L] = l
        # BrickPi.MotorSpeed[R] = r

    def setTouchCallback(self, func):
        self.touchcallback = func

    def getEncoderValues(self):
        # getEncoderValues() -> tuple (x, y)
        return (self.encL, self.encR)

def touchUnitTest(touchcallback=None):
    touchcount = 0
    encL = 0
    encR = 0
    while 1:
        touchcount = abs(touchcount - 1)
        result = BrickPiUpdateValues()
        if not result:
            # Successfully updated values
            if BrickPi.Sensor[S2]:
                # This algorithm is used to prevent misinterpretation
                touchcount += 2
                if touchcount > 8:
                    if touchcallback:
                        touchcallback()
                    touchcount = 0
            # Update Encoder Values
            encL = BrickPi.Encoder[L]
            encR = BrickPi.Encoder[R]
        time.sleep(0.01)

if __name__ == "__main__":
    # Unit Test
    """
    def touchUnitTest(c):
        while 1:
            c.update()
    """
    def isTouched():
        print "S2 Activated"
    """
    con = Controller()
    con.setTouchCallback(isTouched)
    thd = threading.Thread(target=touchUnitTest, args=(con,))
    thd.daemon = True
    thd.start()

    print "Started Controller Instance"
    time.sleep(0.5)
    print "Testing Motors:"
    print "Forward 100"
    con.setMotorSpeed(100, 100)
    time.sleep(2)
    print "Backward 100"
    con.setMotorSpeed(-100, -100)
    time.sleep(2)

    print "Testing Sensors:"
    print "<Press S2 to test callback, strike enter to quit>"
    raw_input()
    """
    mainloop(isTouched)
