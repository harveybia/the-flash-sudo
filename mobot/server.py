import logging
import rpyc
import cv2
from rpyc.utils.server import ThreadedServer

class MobotScv(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        self.cameraCallback = None

    def on_connect(self):
        print "Incoming Conn"
        logging.info("Incoming Connection")

    def on_disconnect(self):
        logging.info("Connection Closed")

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

    def exposed_setCameraCallback(self, func):
        self.cameraCallback = func

    def exposed_getCameraSnapshot(self):
        # Function to return the snapshot taken by camera, in cv2 BGR list form.
        # GrayScale = True
        return cv2.imread('../tests/1.JPG',0)

if __name__ == "__main__":
    server = ThreadedServer(MobotScv, port = 15251)
    server.start()
