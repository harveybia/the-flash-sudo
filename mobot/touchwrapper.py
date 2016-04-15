from BrickPi import *

TOUCH_SENSITIVITY = 20

BrickPiSetup()

BrickPi.SensorType[PORT_1] = TYPE_SENSOR_EV3_TOUCH_0
BrickPiSetupSensors()

while True:
    result = BrickPiUpdateValues()
    if not result:
        button_value = BrickPi.Sensor[PORT_1]
        if button_value > 1000:
            print 'Button reads: %s' % str(button_value)
    time.sleep(0.01)
