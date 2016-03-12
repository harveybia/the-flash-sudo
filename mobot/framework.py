import io
import time
import rpyc
import struct
import socket
import picamera
import threading
from BrickPi import *
from rpyc.utils.server import ThreadedServer
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

# Left and Right Motors:
BrickPi.MotorEnable[L] = 1 # LEFT
BrickPi.MotorEnable[R] = 1 # RIGHT

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

# Global Constants:
FILTER_ORIG   = 0 # Original Video
FILTER_PROC   = 1 # Processed Image (Canny Edges)
FILTER_BW     = 2 # Black & White View
FILTER_IRNV   = 3 # Inverted Image
FILTER_CV     = 4 # Computer Vision Mode, With TRAC PT, BEZIER CURVE
FILTER_PRED   = 5 # Predictive Mode
FILTER_HYBRID = 6 # Hybrid Mode: ORIG + TRAC PT + PRED + CV

FILTER_KEYS   = ['ORIG', 'PROC', 'BW', 'IRNV', 'CV', 'PRED', 'HYBR', 'BLUR']
FILTER_NAMES  = ['original', 'processed', 'black and white', 'inverted',
    'computer vision', 'predictive', 'hybrid', 'blurred']

TASK_IDLE     = 0 # IDLE State
TASK_DEBUG    = 1 # Debug Mode
TASK_TRACE    = 2 # Line Trace
TASK_CAMERA   = 3 # Capture Camera Feed
TASK_TEST     = 4 # Test Trial

TASK_KEYS   = ['IDLE', 'DEBU', 'TRAC', 'CAM', 'TEST']
TASK_NAMES  = ['idle', 'debug', 'line trace', 'camera', 'test']

# Constants for Value slide controls:
SLIDE_KEYS = [
    'BRIG', 'CNST', 'BLUR',
    'THRS', 'SIZE', 'CERT', 'PTS', 'RADI', 'A', 'B', 'C',
    'TCHS', 'GATG', 'MAXS'
    ]

STAT_ONLINE = 22
STAT_DISCONNECTED = 23
STAT_MISSION = 24
STAT_ABORT = 25

def debugConnection(sock, addr, port):
    # Prints the details of a connection
    warn("connection timed out, plesae check listener status")
    print "detailed Report:"
    print term.render("${RED}IP_ADDR: ${GREEN}%s${NORMAL}"%addr)
    print term.render("${RED}PORT: : ${GREEN}%d${NORMAL}"%port)
    if not sock.gettimeout(): return
    print term.render("${RED}connection timed out after %.3f seconds \
        ${NORMAL}" %sock.gettimeout())

def startVideoStream_H264(port, stop_event):
    info("setting up streaming socket")
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', port))
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
        while not stop_event.is_set():
            pass
        CAMERA.stop_recording()
    finally:
        connection.close()
        server_socket.close()

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

        self.loopstop = threading.Event()
        self.loopthd = threading.Thread(target=self.mainloop,
            args=(self.loopstop,))
        self.loopthd.daemon = True

        self.videostop = threading.Event()
        self.videothd = None

    def on_connect(self):
        info("received connection")
        self.loopthd.start()

    def on_disconnect(self):
        warn("connection lost")
        self.loopstop.set()
        self.exposed_stopVideoStream

    def exposed_recognized(self):
        return True

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

    def exposed_startVideoStream(self, port):
        # Establishs a TCP connection with interface for video streaming
        if self.videothd != None:
            warn("video streaming already running")
            return
        self.videothd = threading.Thread(target=startVideoStream_H264,
            args=(port, self.videostop))
        self.videothd.daemon = True
        info("starting video stream")
        self.videothd.start()

    def exposed_stopVideoStream(self):
        info("stopping video stream")
        self.videostop.set()

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
                threshold = int(28 - self.values['TCHS'] * 20)
                self.touchcount += 2
                if self.touchcount > threshold:
                    # Increment gates count
                    self.status['GATC'] += 1
                    # Reset signal strength
                    self.touchcount = 0
            # Update encoder values
            self.encL = BrickPi.Encoder[L]
            self.encR = BrickPi.Encoder[R]

    def mainloop(self, stop_event):
        while not stop_event.is_set():
            self.update()
            # Refresh period
            stop_event.wait(0.05)

if __name__ == "__main__":
    init("initiating mobot server")
    server = ThreadedServer(MobotService, port = MOBOT_PORT)
    server.start()
