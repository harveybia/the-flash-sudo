import picamera
import socket
import time

ADDR, PORT = "", 15252
RESOLUTION = (320, 240)
FRAMERATE = 10

def startServing():
    s = socket.socket()
    s.bind((ADDR, PORT))
    s.listen(0)
    cam = picamera.PiCamera()
    cam.resolution = RESOLUTION
    cam.framerate = FRAMERATE
    cam.start_preview()
    time.sleep(0.5)

    s.listen(0)
    conn = s.accept()[0].makefile('wb')
    cam.start_recording(conn, format='h264')
