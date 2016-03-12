import io
import time
import rpyc
import struct
import socket
import picamera
import threading
from BrickPi import *
from rpyc import ThreadedServer
from utils import init, info, warn

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

# Camera configuration
CAMERA = picamera.PiCamera()
V_WIDTH, V_HEIGHT = 320, 240
FRAMERATE = 24

# Service configuration
MOBOT_PORT = 15112

def debugConnection(sock, addr, port):
    # Prints the details of a connection
    warn("connection timed out, plesae check listener status")
    print "detailed Report:"
    print term.render("${RED}IP_ADDR: ${GREEN}%s${NORMAL}"%addr)
    print term.render("${RED}PORT: : ${GREEN}%d${NORMAL}"%port)
    if not sock.gettimeout(): return
    print term.render("${RED}connection timed out after %.3f seconds \
        ${NORMAL}" %sock.gettimeout())

def startVideoStream_H264(addr, port):
    info("setting up streaming socket")
    server_socket = socket.socket()
    server_socket.bind((addr, port))
    server_socket.listen(0)

    # Make a file-like object out of the connection
    CAMERA.resolution = (V_WIDTH, V_HEIGHT)
    CAMERA.framerate = FRAMERATE
    CAMERA.start_preview()
    time.sleep(0.2)

    connection = server_socket.accept()[0].makefile('wb')
    info("connected to %s for video feed"%(str(server_socket.getpeername())))
    try:
        CAMERA.start_recording(connection, format='h264')
        while not VIDEO_TERMINATE:
            pass
        CAMERA.stop_recording()
    finally:
        connection.close()
        client_socket.close()

class MobotService(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        init("mobot service instance created")

        self.values = {
            'BRIG': 0, 'CNST': 50, 'BLUR': 4,
            'THRS': 150, 'SIZE': 4, 'CERT': 0.7, 'PTS': 5, 'RADI': 6,
                'A': 0.6, 'B': 0.3, 'C': 0.1,
            'TCHS': 0.5, 'GATG': 14, 'MAXS': 100
        }

        self.status = {
            'STAT': STAT_ONLINE, 'ACTT': 0, 'MIST': 0, 'DELY': 0,
            'GATC': 0, 'SPED': 0, 'PROT': 0, 'CVST': STAT_ONLINE,
            'BATT': 100, 'ADDR': socket.gethostname()
        }

        self.vL = 0 # left speed
        self.vR = 0 # right speed
        self.encL = 0 # left encoder
        self.encR = 0 # right encoder

        self.touchcount = 0

        self.loopthd = threading.Thread(target=self.mainloop)
        self.loopthd.daemon = True

    def on_connect(self):
        info("received connection")

    def on_disconnect(self):
        warn("connection lost")

    def exposed_getMobotStatus(self):
        self._updateStatus()
        return self.status

    def exposed_configureSettings(self, values):
        # @param:
        # values: (dict) the dictionary of setting values
        try:
            for key in self.values:
                self.values[key] = values[key]
        except:
            warn("invalid options in configureSettings()")

    def exposed_startVideoStream(self, addr, port):
        # Establishs a TCP connection with interface for video streaming
        startVideoStream_H264(addr, port)

    def _updateStatus(self):
        # Polls device information and updates status dict
        pass

    def _setMotorSpeed(self, l, r):
        if abs(l) > 255 or abs(r) > 255:
            raise ParameterInvalidException("Invalid motor speeds")
        self.vL = l; self.vR = r
        # BrickPi.MotorSpeed[L] = l
        # BrickPi.MotorSpeed[R] = r

    def exposed_setMotorSpeed(self, l, r):
        self._setMotorSpeed(l, r)

    def update(self):
        self.touchcount = abs(self.touchcount - 1)
        BrickPi.MotorSpeed[L] = self.vL
        BrickPi.MotorSpeed[R] = self.vR
        result = BrickPiUpdateValues()
        if not result:
            # Successfully updated values
            # Read touch sensor values
            if BrickPi.Sensor[S2]:
                # Prevent signal disturbances
                threshold = int(28 - self.status['TCHS'] * 20)
                self.touchcount += 2
                if self.touchcount > threshold:
                    # Increment gates count
                    self.status['GATC'] += 1
                    # Reset signal strength
                    self.touchcount = 0
            # Update encoder values
            self.encL = BrickPi.Encoder[L]
            self.encR = BrickPi.Encoder[R]

    def mainloop(self):
        while 1:
            self.update()
            # Refresh period
            time.sleep(0.05)

if __name__ == "__main__":
    init("initiating mobot server")
    server = ThreadedServer(MobotService, port = MOBOT_PORT)
    server.start()
