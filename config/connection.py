import rpyc
import socket
import cv2
import numpy as np
import threading
import time

# My Cam Listener TCP addr
TCP_IP = socket.gethostname()
TCP_PORT = 15112
terminated = False
global transmitting
transmitting = False

# Server addr, should be raspi
ADDR, PORT = "128.237.141.170", 15251

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def listenToCam():
    global transmitting
    transmitting = True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", TCP_PORT))
    print "listening to %s:%d"%(TCP_IP, TCP_PORT)
    s.listen(True)
    conn, addr = s.accept()
    print "accepted connection from %s"%str(addr)

    length = recvall(conn, 8000)
    stringData = recvall(conn, int(length))

    data = np.fromstring(stringData, dtype='uint8')
    img = cv2.imdecode(data, 1)

    # Test Code
    cv2.imshow('Server', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print "closing socket"
    s.close()
    transmitting = False

c = rpyc.connect(ADDR, PORT)
c.root.configureVideoStream(TCP_IP, TCP_PORT)
while not terminated:
    global transmitting
    T = threading.Thread(target=listenToCam)
    T.daemon = True
    T.start()
    while transmitting:
        pass
    # Close connection
    time.sleep(2)
    print "fetching camera snapshot"
    c.root.getCameraSnapshot()
