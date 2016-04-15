import time
from i2clibraries import i2c_hmc5883l

# A value greater than this will be perceived as inclined down
INCLINE_THRESHOLD = -20
MAGNETIC_DECLINATION = (-9, -18)

hmc5883l = i2c_hmc5883l.hmc5883l(declination = MAGNETIC_DECLINATION)

def getMobotAttitude():
    return hmc5883l.axes()

def getMobotInclined():
    x, y, z = getMobotAttitude()
    if z > INCLINE_THRESHOLD:
        return True
    else:
        return False

if __name__ == "__main__":
    while 1:
        print getMobotAttitude()
        print getMobotInclined()
        time.sleep(0.5)
