import logging
import rpyc
import time
import cv2
import io
import numpy as np
import picamera
import easyterm
import socket
import rpyc
from rpyc.utils.server import ThreadedServer

# This is the mobot Backend Service
# Can expose service locally for algorithmic clients to send Instructions

# IP Address for camera data stream host target
TCP_IP = '128.237.138.121'
TCP_PORT = 15122
STREAM = io.BytesIO()
CAMERA = picamera.PiCamera()

term = easyterm.TerminalController()

def info(msg):
    print time.ctime()[11:19], \
        term.render("${GREEN}[INFO]${NORMAL}", \
        term.render("${YELLOW}%s${NORMAL}"%msg)

def warn(msg):
    print time.ctime()[11:19], \
        term.render("${RED}${BG_WHITE}[WARN]${NORMAL}", \
        term.render("${RED}%s${NORMAL}"%msg)

def debugConnection(sock, addr, port):
    warn("connection timed out, plesae check listener status")
    print "detailed Report:"
    print term.render("${RED}IP_ADDR: ${GREEN}%s${NORMAL}"%addr)
    print term.render("${RED}PORT: : ${GREEN}%d${NORMAL}"%port)
    print term.render("${RED}connection timed out after %.3f seconds \
        ${NORMAL}" %sock.gettimeout())

class MobotScv(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        info("starting camera preview, calibrating color")
        CAMERA.start_preview()
        info("preview complete, capturing footage into stream")
        CAMERA.capture(STREAM, format='jpeg', resize=(320, 240))

        self.connected = False

    @staticmethod
    def getCameraSnapshot():
        # Returns the snapshot array with BGR in OpenCV nparray format
        data = np.fromstring(STREAM.getvalue(), dtype=np.uint8)
        return cv2.imdecode(data, 1)

    def on_connect(self):
        info("connection established")

    def on_disconnect(self):
        info("connection lost")

    def exposed_configureVideoStream(self, addr, port):
        TCP_IP = addr
        TCP_PORT = port
        info("configured cam stream addr: %s, port: %d"%(TCP_IP, TCP_PORT))
        """
        if not self.connected:
            try:
                sock.connect((TCP_IP, TCP_PORT))
                self.connected = True
            except socket.timeout:
                debugConnection(TCP_IP, TCP_PORT)
        """

    def exposed_getBattery(self):
        return 100

    def exposed_getIntegrity(self):
        return 100

    def exposed_getCameraConfig(self):
        return {
            "CAMERA_ENABLED": True,
            "CAMERA_X_OFFSET": 10,
            "CAMERA_Y_OFFSET": -10,
            "CAMERA_MOUNT_ANGLE": 45
            }

    def exposed_getCameraSnapshot(self):
        # This function will not return any value
        # It invokes a signal to send snapshot via TCP/IP Protocol
        # It will probably block the main thread
        # GrayScale = True
        sock = socket.socket()
        info("trying to connect to %s:%d"%(TCP_IP, TCP_PORT))
        try:
            sock.connect((TCP_IP, TCP_PORT))
        except:
            debugConnection(sock, TCP_IP, TCP_PORT)
            return

        info("cam snapshot requested")
        img = MobotScv.getCameraSnapshot()

        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
        result, imgencode = cv2.imencode('.jpg', img, encode_param)
        data = np.array(imgencode)
        stringData = data.tostring()

        try:
            sock.send(str(len(stringData)).ljust(16))
            sock.send(stringData)
            info("snapshot sent successfully")
        except socket.timeout:
            debugConnection(sock, TCP_IP, TCP_PORT)

        info("closing socket")
        sock.close()

if __name__ == "__main__":
    server = ThreadedServer(MobotScv, port = 15251)
    server.start()
