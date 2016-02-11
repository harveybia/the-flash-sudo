import logging
import rpyc
import time
import cv2
import io
import numpy as np
import picamera
import struct
import easyterm
import socket
import rpyc
import threading
from rpyc.utils.server import ThreadedServer

# This is the mobot Backend Service
# Can expose service locally for algorithmic clients to send Instructions

CAMERA = picamera.PiCamera()

term = easyterm.TerminalController()

def init(msg):
    print time.ctime()[11:19], \
        term.render("${GREEN}${BG_WHITE}[INIT]${NORMAL}"), \
        term.render("${YELLOW}%s${NORMAL}"%msg)

def info(msg):
    print time.ctime()[11:19], \
        term.render("${GREEN}[INFO]${NORMAL}"), \
        term.render("${YELLOW}%s${NORMAL}"%msg)

def warn(msg):
    print time.ctime()[11:19], \
        term.render("${RED}${BG_WHITE}[WARN]${NORMAL}"), \
        term.render("${RED}%s${NORMAL}"%msg)

def debugConnection(sock, addr, port):
    warn("connection timed out, plesae check listener status")
    print "detailed Report:"
    print term.render("${RED}IP_ADDR: ${GREEN}%s${NORMAL}"%addr)
    print term.render("${RED}PORT: : ${GREEN}%d${NORMAL}"%port)
    if not sock.gettimeout(): return
    print term.render("${RED}connection timed out after %.3f seconds \
        ${NORMAL}" %sock.gettimeout())

#http://picamera.readthedocs.org/en/release-1.10/recipes1.html#stream-capture
def startVideoStream(ADDR, PORT):
    # Connect a client socket to my_server:8000 (change my_server to the
    # hostname of your server)
    info("connecting to %s:%d"%(ADDR, PORT))
    client_socket = socket.socket()
    client_socket.connect((ADDR, PORT))
    info("connection successful")

    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    try:
        CAMERA.resolution = (640, 480)
        # Start a preview and let the camera warm up for 2 seconds
        CAMERA.start_preview()
        time.sleep(2)

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep
        # our protocol simple)
        start = time.time()
        stream = io.BytesIO()
        info("continuously serving data")
        for foo in CAMERA.capture_continuous(stream, 'jpeg'):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            # Rewind the stream and send the image data over the wire
            stream.seek(0)
            connection.write(stream.read())
            # If we've been capturing for more than 30 seconds, quit
            if time.time() - start > 30:
                break
            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
        # Write a length of zero to the stream to signal we're done
        connection.write(struct.pack('<L', 0))
    finally:
        warn("error occurred, closing socket")
        connection.close()
        client_socket.close()

class MobotScv(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        info("starting camera preview, calibrating color")
        CAMERA.start_preview()
        info("preview complete, capturing footage into stream")
        self.stream = io.BytesIO()
        self.stream_thread = None

        CAMERA.capture(self.stream, format='jpeg', resize=(320, 240))

        self.connected = False
        # IP Address for camera data stream host target
        self.TCP_IP = "128.237.138.121"
        self.TCP_PORT = 15122

    def getCameraSnapshot(self):
        # Returns the snapshot array with BGR in OpenCV nparray format
        self.stream = io.BytesIO()
        CAMERA.capture(self.stream, format='jpeg', resize=(320, 240))
        data = np.fromstring(self.stream.getvalue(), dtype=np.uint8)
        return cv2.imdecode(data, 1)

    def on_connect(self):
        info("connection established")

    def on_disconnect(self):
        info("connection lost")

    def exposed_configureVideoStream(self, addr, port):
        self.TCP_IP = addr
        self.TCP_PORT = port
        info("configured cam stream addr: %s, port: %d" \
            %(self.TCP_IP, self.TCP_PORT))

    def exposed_startVideoStream(self):
        info("starting to serve video stream")
        time.sleep(0.5)
        self.stream_thread = threading.Thread(target=startVideoStream,
            args=(self.TCP_IP, self.TCP_PORT))
        self.stream_thread.daemon = True
        self.stream_thread.start()
        info("video stream thread initiated")

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
        sock.settimeout(5.0)
        info("trying to connect to %s:%d"%(self.TCP_IP, self.TCP_PORT))
        sock.connect((self.TCP_IP, self.TCP_PORT))

        info("cam snapshot requested")
        img = self.getCameraSnapshot()

        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
        result, imgencode = cv2.imencode('.jpg', img, encode_param)
        data = np.array(imgencode)
        stringData = data.tostring()

        try:
            sock.send(str(len(stringData)).ljust(16))
            sock.send(stringData)
            info("snapshot sent successfully")
        except socket.timeout:
            debugConnection(sock, self.TCP_IP, self.TCP_PORT)

        info("closing socket")
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

if __name__ == "__main__":
    init("initiating server")
    server = ThreadedServer(MobotScv, port = 15251)
    server.start()
