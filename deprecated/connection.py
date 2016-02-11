import rpyc
import socket
import cv2
import numpy as np
import threading
import time
from multiprocessing.pool import ThreadPool

# My Cam Listener TCP addr
TCP_IP = socket.gethostname()
TCP_PORT = 15112
terminated = False

# Server addr, should be raspi
ADDR, PORT = "128.237.141.170", 15251
#ADDR, PORT = "localhost", 15251

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

class Listener():
    def __init__(self):
        self.transmitting = False
        self.processed = True
        self.terminated = False
        self.c = rpyc.connect(ADDR, PORT)
        self.c.root.configureVideoStream(TCP_IP, TCP_PORT)
        self.image = None

    def listenToCam(self):
        self.transmitting = True
        self.processed = False

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(("", TCP_PORT))
        print "listening to %s:%d"%(TCP_IP, TCP_PORT)
        self.s.listen(True)
        print "listen invoked"
        self.transmitting = False

        conn, addr = self.s.accept()
        print "accepted connection from %s"%str(addr)

        length = recvall(conn, 16)
        print "length: %d"%int(length)
        stringData = recvall(conn, int(length))

        data = np.fromstring(stringData, dtype='uint8')
        img = cv2.imdecode(data, 1)

        # Test Code
        print "got image"
        """
        cv2.imshow('Server', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """
        print "closing socket"
        try:
            self.s.shutdown(socket.SHUT_RDWR)
            print "showdown invoked"
        except:
            pass
        self.s.close()
        self.processed = True
        self.image = img

def fetchCallback(arg):
    print "image ready"

if __name__ == "__main__":
    l = Listener()
    while not l.terminated:

        T = threading.Thread(target=l.listenToCam)
        T.daemon = True
        T.start()

        #pool = ThreadPool(processes=1)
        #async_img = pool.apply_async(l.listenToCam, callback=fetchCallback)
        while l.transmitting:
            time.sleep(0.001)
        print "TCP listening: %s:%d"%(TCP_IP, TCP_PORT)
        print "fetehing camera snapshot"
        l.c.root.getCameraSnapshot()
        while not l.processed:
            time.sleep(0.001)

        #l.s.shutdown()
        time.sleep(2)

        #img = async_img.get()
        img = l.image
        ##print img.size
        cv2.imshow('Server', img)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        cv2.waitKey(1)
        print "process completed"

"""
c = rpyc.connect(ADDR, PORT)
c.root.configureVideoStream(TCP_IP, TCP_PORT)
while not terminated:
    T = threading.Thread(target=listenToCam)
    T.daemon = True
    T.start()
    while transmitting:
        pass
    # Close connection
    time.sleep(2)
    print "fetching camera snapshot"
    c.root.getCameraSnapshot()
"""
