import time
from i2clibraries import i2c_hmc5883l

hmc5883l = i2c_hmc5883l.hmc5883l()

def getMobotAttitude():
    return hmc5883l.axes()

if __name__ == "__main__":
    while 1:
        print getMobotAttitude()
        time.sleep(0.5)
