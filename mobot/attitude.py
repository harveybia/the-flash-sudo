import time
from i2clibraries import i2c_hmc5883l

hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)

hmc5883l.setContinuousMode()
# hmc5883l.setDeclination(9,54)

def getMobotAttitude():
    return hmc5883l.getAxes

if __name__ == "__main__":
    while 1:
        print(getMobotAttitude())
        time.wait(0.5)
