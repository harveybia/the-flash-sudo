import RPi.GPIO as GPIO
import time
import os

buttonPin = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonPin, GPIO.IN)

while True:
    if (GPIO.input(buttonPin)):
        # Call script and run!
        os.system('echo script initializing.')
        os.system('sudo python /home/pi/Desktop/the-flash-sudo/mobot/framework.py -k -t -s')
        os.system('echo script ended.')
