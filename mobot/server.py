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

sock = socket.socket()
sock.connect((TCP_IP, TCP_PORT))

term = easyterm.TerminalController()

def info(msg):
    print time.ctime(),
        " INFO: ", term.render("${YELLOW}%s${NORMAL}"%msg)

def warn(msg):
    print time.ctime(),
        " WARN: ", term.render("${RED}${BG_WHITE}%s${NORMAL}"%msg)

class MobotScv(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        info("starting camera preview, salibrating Color")
        CAMERA.start_preview()
        info("preview complete, capturing footage into stream")
        CAMERA.capture(STREAM, format='jpeg', resize=(320, 240))

    @staticmethod
    def getCameraSnapshot():
        # Returns the snapshot array with BGR in OpenCV nparray format
        data = np.fromstring(STREAM.getvalue(), dtype=np.utf8)
        return cv2.imdecode(data, 1)

    def on_connect(self):
        info("connection established")

    def on_disconnect(self):
        info("connection lost")

    def exposed_configureVideoStream(self, addr, port):
        TCP_IP = addr
        TCP_PORT = port
        info("configured cam stream addr: %s, port: %d"%(TCP_IP, TCP_PORT))

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
            warn("connection timed out, plesae check listener status")
            print "detailed Report:"
            print term.render("${RED}IP_ADDR: ${GREEN}%s${NORMAL}"%TCP_IP)
            print term.render("${RED}PORT: : ${GREEN}%d${NORMAL}"%TCP_PORT)
            print term.render("${RED}connection timed out after %.3f seconds \
                ${NORMAL}" %sock.gettimeout())
        info("closing socket")
        sock.close()

if __name__ == "__main__":
    server = ThreadedServer(MobotScv, port = 15251)
    server.start()
