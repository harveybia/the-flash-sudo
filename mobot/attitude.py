import time
from i2clibraries import i2c_hmc5883l

INCLINE_THRESHOLD = 420
hmc5883l = i2c_hmc5883l.hmc5883l()

def getMobotAttitude():
    return hmc5883l.axes()

def getMobotInclined():
    (x,y,z) = getMobotAttitude()
    inclineVal = abs(y)
    if abs(inclineVal - INCLINE_THRESHOLD) <= 50:
        return False


if __name__ == "__main__":
    while 1:
        print getMobotAttitude()
        print hmc5883l.heading()
        print hmc5883l.degrees(0)
        time.sleep(0.5)
