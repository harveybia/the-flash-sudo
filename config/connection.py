import rpyc
import socket
import cv2
import numpy as np
import threading
import io
import time
import struct
from PIL import Image
from multiprocessing.pool import ThreadPool

# My Cam Listener TCP addr
TCP_IP = socket.gethostname()
TCP_PORT = 15112
terminated = False

# Server addr, should be raspi
ADDR, PORT = "128.237.174.4", 15251
VIDEO_PORT = 15252
#ADDR, PORT = "localhost", 15251

if __name__ == "__main__":
    # Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
    # all interfaces)
    c = rpyc.connect(ADDR, PORT)
    c.root.startVideoStream_H264()

    #video = cv2.VideoCapture('tcp://%s:%d/'%(ADDR, VIDEO_PORT))
    #while True:
        #ret, frame = video.read()
        #print type(frame)
        #print frame
        #cv2.imshow("SERVER", frame)
        #if cv2.waitKey(1) == ord('q'):
            #break
