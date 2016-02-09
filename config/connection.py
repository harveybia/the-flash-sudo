import rpyc
import socket
import cv2
import numpy as np
import threading

# My Cam Listener TCP addr
TCP_IP = socket.gethostname()
TCP_PORT = 15122
terminated = False
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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    print "listening to %d:%d"%(TCP_IP, TCP_PORT)
    s.listen(True)
    conn, addr = s.accept()
    transmitting = True
    print "accepted connection from %s"%addr

    length = recvall(conn, 16)
    stringData = recvall(conn, int(length))

    data = np.fromstring(stringData, dtype='uint8')
    img = cv2.imdecode(data, 1)

    transmitting = False
    # Test Code
    cv2.imshow('Server', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

while not terminated:
    c = rpyc.connect(ADDR, PORT)
    c.root.configureVideoStream(TCP_IP, TCP_PORT)
    while transmitting:
        pass
    # Close connection
    time.sleep(2)
    s.close()
