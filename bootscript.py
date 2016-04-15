import RPi.GPIO as GPIO
import time
import os
import sys

buttonPin = 21
exitButtonPin = 20
GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonPin, GPIO.IN)
GPIO.setup(exitButtonPin, GPIO.IN)

while True:
    if (not GPIO.input(buttonPin)):
        # Call script and run!
        os.system('echo script initializing.')
        os.system('sudo python /home/pi/Desktop/the-flash-sudo/mobot/framework.py -k -t -s')
        os.system('echo script ended.')

    elif (not GPIO.input(exitButtonPin)):
        # Exit! Leave process to login shell.
        os.system('echo script aborted')
        sys.exit(0)
