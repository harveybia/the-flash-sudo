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
ADDR, PORT = "128.237.141.170", 15251
#ADDR, PORT = "localhost", 15251

if __name__ == "__main__":
    # Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
    # all interfaces)
    c = rpyc.connect(ADDR, PORT)
    c.root.configureVideoStream(TCP_IP, TCP_PORT)
    c.root.startVideoStream_H264()

    video = cv2.VideoCapture('tcp://%s:%d'%(TCP_IP, TCP_PORT))
    try:
        while True:
            ret, frame = video.read()
            cv2.imshow("SERVER", frame)
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        connection.close()
        server_socket.close()
