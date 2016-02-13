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

    server_socket = socket.socket()
    server_socket.bind(('', TCP_PORT))
    server_socket.listen(0)

    c.root.startVideoStream()
    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    try:
        while True:
            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            image_len = struct.unpack('<L', \
                connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            image_stream.seek(0)

            data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
            # "Decode" the image from the array, preserving colour
            image = cv2.imdecode(data, 1)
            cv2.imshow("SERVER", image)
            cv2.waitKey(1)
    finally:
        connection.close()
        server_socket.close()
