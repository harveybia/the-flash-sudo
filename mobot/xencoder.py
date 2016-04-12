import time
from BrickPi import *

BrickPiSetup()

BrickPi.MotorEnable[PORT_A] = 1
BrickPiSetupSensors()

class TimePosition():
    # The class representing position and time at one spacetime instance
    def __init__(self, time=0.0, position=0):
        # @param
        # time: (float) the time corresponding to that position
        # position: (int) the position in degree of the motor
        self.time = float(time)
        self.position = int(position)

    def __repr__(self):
        return "<TimePosition>: (%.3fs, %d)"%(self.time, self.position)

    def avgSpeedFrom(self, other):
        result = 0.0
        if self.time != other.time:
            result = (self.position - other.position) / (self.time - other.time)
            result /= 10
        return result

class Motor():
    def __init__(self, port=PORT_A):
        self.port = port
        self.position = 0
        self.power = 0

        self.targetspeed = 50
        self.p = 1
        self.i = 0
        self.d = 1
        self.errorsum = 0
        self.preverr = 0

        self.currentTP = TimePosition(time.time(), 0)
        self.previousTP = self.currentTP

        # Set the base position to current position, track delta later
        self.baseposition = 0

    def getActualSpeed(self):
        return self.currentTP.avgSpeedFrom(self.previousTP)

    def setZeroPosition(self):
        # Reset the zero position to current position
        self.baseposition += self.currentTP.position

    def updatePosition(self, newPosition):
        # Called by the framework when the BrickPi provides a new motor position.
        self.previousTP = self.currentTP
        self.currentTP = TimePosition(time.time(),
            newPosition - self.baseposition)

    def run(self):
        while True:
            result = BrickPiUpdateValues()
            if not result:
                self.updatePosition(BrickPi.Encoder[PORT_A])
                # cnt_value = (BrickPi.Encoder[PORT_A] % 720) / 2
                err = self.getActualSpeed() - self.targetspeed
                pterm = err * self.p
                self.errorsum += err
                iterm = self.errorsum * self.i
                dterm = (err - self.preverr) * self.d
                self.preverr = err

                speed = int(-pterm + iterm + dterm)

                print (pterm, iterm, dterm)
                print self.getActualSpeed()
                print speed
                print self.currentTP
                print "-----------"

                BrickPi.MotorSpeed[PORT_A] = speed
            time.sleep(0.05)

print "Done."

a = Motor()
a.run()

#!/usr/bin/env python
# Jaikrishna
# Initial Date: June 24, 2013
# Last Updated: June 24, 2013
#
# These files have been made available online through a Creative Commons Attribution-ShareAlike 3.0  license.
# (http://creativecommons.org/licenses/by-sa/3.0/)
#
# http://www.dexterindustries.com/
# This code is for testing the BrickPi with a Lego Motor

from BrickPi import *   #import BrickPi.py file to use BrickPi operations

BrickPiSetup()  # setup the serial port for communication

BrickPi.MotorEnable[PORT_A] = 1     #Enable the Motor A
BrickPi.MotorSpeed[PORT_A] = 200    #Set the speed of MotorA (-255 to 255)

BrickPiSetupSensors()       #Send the properties of sensors to BrickPi

while True:
    result = BrickPiUpdateValues()  # Ask BrickPi to update values for sensors/motors
    if not result :                 # if updating values succeeded
        print ( BrickPi.Encoder[PORT_A] %720 ) /2   # print the encoder degrees
    time.sleep(.1)      #sleep for 100 ms

# Note: One encoder value counts for 0.5 degrees. So 360 degrees = 720 enc. Hence, to get degress = (enc%720)/2


# Motor and associated classes, representing a motor attached to one of the BrickPi ports.
#
# Copyright (c) 2014 Charles Weir.  Shared under the MIT Licence.

from Scheduler import Scheduler
import logging

class PIDSetting():
    '''Settings for the PID servo algorithm.  These may differ between motors.  The default values are here.

    Distances are in clicks, times in ms, motor power between -255 and +255, the sum of distance is added 20 times/sec.
    Speeds in clicks per second.
    '''
    def __init__(self,distanceMultiplier=0.9,speedMultiplier=0.23,integratedDistanceMultiplier=(0.05/20.0),
                 closeEnoughPosition=4, closeEnoughSpeed=10.0):
        #: Factor for motor power as function of distance - in power units per click distance.
        self.distanceMultiplier = distanceMultiplier
        #: Factor for motor power as function of speed - in power units per (click per millisecond)
        self.speedMultiplier = speedMultiplier
        #: Factor for motor power as a function of the integrated distance - in power units per (click-millisecond)
        self.integratedDistanceMultiplier = integratedDistanceMultiplier
        #: Distance in clicks from the target that we'll accept as got there.
        self.closeEnoughPosition = closeEnoughPosition
        #: Speed that we'll consider as close enough to zero.
        self.closeEnoughSpeed = closeEnoughSpeed


    def __repr__(self):
        return "PID Setting (distanceMultiplier=%3.4f, speedMultiplier=%3.4f, integratedDistanceMultiplier=%3.4f)" % (self.distanceMultiplier,
                                                                        self.speedMultiplier, self.integratedDistanceMultiplier)


class TimePosition():
    "Represents a motor position at a specific time.  Time in milliseconds, position in clicks."
    def __init__(self,time=0.0,position=0):
        #: Time created
        self.time = float(time)
        #: Position at that time
        self.position = int(position)

    def __repr__(self):
        return "TimeDist (%.3f, %d)" % (self.time, self.position)

    def averageSpeedFrom(self, other):
        'Answers the speed in clicks per second coming to this point from other'
        result = 0.0
        if self.time != other.time:
            result = 1000.0 * (self.position - other.position) / (self.time - other.time)
        return result

class Motor():
    '''An NXT motor connected to a BrickPi port.

    A motor is identified by its idChar ('A' through 'D').
    It has a current position, relative to the basePosition it has set, and a current speed.

    It also defines coroutines to position it using the standard PID servo motor algorithm, and
    to run at a specific speed.
    '''
    def timeMillis(self):
        # Answers the current time - member function so we can mock it easily for testing.
        return Scheduler.currentTimeMillis()

    def __init__(self, port, scheduler = None):
        self.port = port
        #: Identifier for the motor
        self.idChar = chr(port + ord('A'))
        self._enabled = False
        self._position = 0
        self._power = 0
        self.pidSetting = PIDSetting()
        self.currentTP = self.previousTP = TimePosition(0, self.timeMillis())
        self.scheduler = scheduler
        self.basePosition = 0

    def setPIDSetting( self, pidSetting ):
        'Sets the parameters for the PID servo motor algorithm'
        self.pidSetting = pidSetting
    def setPower(self, p):
        'Sets the power to be sent to the motor'
        self._power = int(p)
    def power(self):
        'Answers the current power setting'
        return self._power
    def position(self):
        'Answers the current position'
        return self.currentTP.position
    def enabled(self):
        'Answers true if the motor is enabled'
        return self._enabled
    def enable(self, whether):
        'Sets whether the motor is enabled'
        self._enabled = whether

    def zeroPosition(self):
        'Resets the motor base for its position to the current position.'
        self.basePosition += self.position()

    def speed(self):
        'Answers the current speed calculated from the latest two position readings'
        return self.currentTP.averageSpeedFrom( self.previousTP )

    def __repr__(self):
        return "Motor %s (location=%d, speed=%f)" % (self.idChar, self.position(), self.speed())

    def updatePosition(self, newPosition):
        # Called by the framework when the BrickPi provides a new motor position.
        self.previousTP = self.currentTP
        self.currentTP = TimePosition( self.timeMillis(), newPosition - self.basePosition )

    def stopAndDisable(self):
        'Stops and disables the motor'
        self.setPower(0)
        self.enable(False)
        logging.info("Motor %s stopped" % (self.idChar))

    def moveTo( self, *args, **kwargs ):
        'Alternative name for coroutine positionUsingPIDAlgorithm'
        return self.positionUsingPIDAlgorithm( *args, **kwargs )

    def positionUsingPIDAlgorithm( self, target, timeoutMillis = 3000 ):
        'Coroutine to move the motor to position *target*, stopping after *timeoutMillis* if it hasnt reached it yet'
        return self.scheduler.withTimeout( timeoutMillis, self.positionUsingPIDAlgorithmWithoutTimeout( target ) )

    def positionUsingPIDAlgorithmWithoutTimeout( self, target ):
        'Coroutine to move the motor to position *target*, using the PID algorithm with the current PIDSettings'
        distanceIntegratedOverTime = 0 # I bit of PID.
        self.enable(True)
        logging.info( "Motor %s moving to %d" % (self.idChar, target) )
        try:
            while True:
                delta = (target - self.currentTP.position)
                distanceIntegratedOverTime += delta * (self.currentTP.time - self.previousTP.time)
                speed = self.speed()

                if abs(delta) <= self.pidSetting.closeEnoughPosition and abs(speed) < self.pidSetting.closeEnoughSpeed:
                    break # Near enough - finish.

                power = (self.pidSetting.distanceMultiplier * delta
                         - self.pidSetting.speedMultiplier * speed
                         + self.pidSetting.integratedDistanceMultiplier * distanceIntegratedOverTime )
                self.setPower( power )

                yield

        finally:
            self.stopAndDisable()


    def setSpeed( self, targetSpeedInClicksPerSecond, timeoutMillis = 3000 ):
        'Coroutine to run the motor at constant speed *targetSpeedInClicksPerSecond* for time *timeoutMillis*'
        return self.scheduler.withTimeout( timeoutMillis, self.runAtConstantSpeed( targetSpeedInClicksPerSecond ) )

    def runAtConstantSpeed( self, targetSpeedInClicksPerSecond ):
        '''Coroutine to run the motor at constant speed *targetSpeedInClicksPerSecond*
        '''
        # TODO: Algorithm needs work.
        #       Seems to hunt rather than stick at a fixed speed, and magic numbers should be configurable.
        speedErrorMargin = 10
        power = 20.0
        if targetSpeedInClicksPerSecond < 0:
            power = -power
        self.enable(True)
        logging.info( "Motor %s moving at constant speed %.3f" % (self.idChar, targetSpeedInClicksPerSecond) )
        try:
            while abs(targetSpeedInClicksPerSecond - 0.0) > speedErrorMargin: # Don't move if the target speed is zero.
                speed = self.speed()
                if abs(speed - targetSpeedInClicksPerSecond) < speedErrorMargin:
                    pass
                elif abs(speed) < abs(targetSpeedInClicksPerSecond):
                    power *= 1.1
                elif abs(speed) > abs(targetSpeedInClicksPerSecond):
                    power /= 1.1
                self.setPower( power )

                yield

        finally:
            self.stopAndDisable()
