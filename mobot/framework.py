#####################################
# Core Algorithm and Mobot Platform #
# copyright 2015-2016 Harvey Shi    #
#####################################
flash = \
"""
  __  .__                       _____.__                .__
_/  |_|  |__   ____           _/ ____\  | _____    _____|  |__
\   __\  |  \_/ __ \   ______ \   __\|  | \__  \  /  ___/  |  \\
 |  | |   Y  \  ___/  /_____/  |  |  |  |__/ __ \_\___ \|   Y  \\
 |__| |___|  /\___  >          |__|  |____(____  /____  >___|  /
           \/     \/                           \/     \/     \/
"""

import io
import cv2
import sys
import time
import math
import rpyc
import getopt
import struct
import socket
import picamera
import threading
import linecache
import processing
import numpy as np
import RPi.GPIO as GPIO
from PIL import Image
from BrickPi import *
from rpyc.utils.server import ThreadedServer
from utils import init, info, warn, term2

STABLE_MODE = True
# The following two constants are overridden manually via command line
# Usage: framework.py (-s (-m <mode>))
STANDALONE = False
# Manual CV Mode override: This only applies to standalone runtime version
# alpha: Matthew's algorithm, based on histogram
# beta: Harvey's algorithm, based on probabilistic model
CV_MANUAL_MODE = 'alpha'
# MANUAL_IRNV will result in tracking black line instead of white line
CV_MANUAL_IRNV = False

# Reference: BrickPi_Python/Sensor_Examples/*.py
# Reference: http://picamera.readthedocs.org/en/release-1.10/recipes1.html

# Setup serial port for communications
BrickPiSetup()

# Aliasing for ports for convenience
L = PORT_B
L1 = PORT_A
R = PORT_C
R1 = PORT_D
S2 = PORT_4

# Pre-coded choices for loops (right or left)
LOOP_CHOICES = ['L'] # Decision Making: all left loops

# Exceptions
class ParameterInvalidException(Exception):
    def __init__(self, description):
        self.des = description

    def __str__(self):
        return repr(self.des)

def echoException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(
        filename, lineno, line.strip(), exc_obj)

# Left and Right Motors:
BrickPi.MotorEnable[L] = 1 # LEFT
BrickPi.MotorEnable[R] = 1 # RIGHT
BrickPi.MotorEnable[L1] = 1 # LEFT
BrickPi.MotorEnable[R1] = 1 # RIGHT

# Touch Sensor Initialization:
BrickPi.SensorType[S2] = TYPE_SENSOR_EV3_TOUCH_DEBOUNCE

# Send properties of sensors to BrickPi
BrickPiSetupSensors()

# Camera configuration
CAMERA = picamera.PiCamera()
V_WIDTH, V_HEIGHT = 320, 240
FRAMERATE = 7

# Const Image Crop Parameters:
VERT_EXC_UP = 0.0 # 0.48
VERT_EXC_DOWN = 0.07
HORI_EXC_L = 0.0
HORI_EXC_R = 0.0

# PID Control Pre-cast Variables
CTRL_P = 1.8
CTRL_I = 0.0005
CTRL_D = 0.5

# Motor speed configuration
MOTOR_BASESPEED = 255

# Ramp move constants
# TODO: Trials will determine the parameters to be used on ramp
RAMP_P = 1.5
RAMP_I = 0.0005
RAMP_D = 0.5
RAMP_BASESPEED = 150
RAMP_BTN = 21 # GPIO Port
ABORT_BTN = 20 # GPIO Abort Signal
GPIO.setmode(GPIO.BCM)
GPIO.setup(RAMP_BTN, GPIO.IN)
GPIO.setup(ABORT_BTN, GPIO.IN)

# Alphacv algorithm configuration
# WARNING: Algorithm is non-linear, increasing number would result in
#          non-determinant polynominal time!
ALPHACV_INTERVAL = 15
ALPHACV_PT_COUNT = 10
# Whether CV skips one row to find curve (deals with unpainted area)
ALPHA_CV_ROW_SKIP = False
ALPHA_CV_CHOOSE_THIN = False

# Service configuration
LOCAL_ADDR = socket.getfqdn()
MOBOT_PORT = 15112

# Global Constants:
CV_BLUR_FACTOR = 4

FILTER_ORIG   = 0 # Original Video
FILTER_PROC   = 1 # Processed Image (Canny Edges)
FILTER_BW     = 2 # Black & White View
FILTER_IRNV   = 3 # Inverted Image
FILTER_CV     = 4 # Computer Vision Mode, With TRAC PT, BEZIER CURVE
FILTER_PRED   = 5 # Predictive Mode
FILTER_HYBRID = 6 # Hybrid Mode: ORIG + TRAC PT + PRED + CV

FILTER_KEYS   = ['ORIG', 'PROC', 'BW', 'IRNV', 'CV', 'PRED', 'HYBR', 'BLUR']
FILTER_NAMES  = ['original', 'processed', 'black and white', 'inverted',
    'computer vision', 'predictive', 'hybrid', 'blurred']

TASK_IDLE     = 0 # IDLE State
TASK_DEBUG    = 1 # Debug Mode
TASK_TRACE    = 2 # Line Trace
TASK_CAMERA   = 3 # Capture Camera Feed
TASK_TEST     = 4 # Test Trial

TASK_KEYS   = ['IDLE', 'DEBU', 'TRAC', 'CAM', 'TEST']
TASK_NAMES  = ['idle', 'debug', 'line trace', 'camera', 'test']

# Constants for Value slide controls:
SLIDE_KEYS = [
    'BRIG', 'CNST', 'BLUR',
    'THRS', 'SIZE', 'CERT', 'PTS', 'RADI', 'A', 'B', 'C',
    'TCHS', 'GATG', 'MAXS'
    ]

STAT_ONLINE = 22
STAT_DISCONNECTED = 23
STAT_MISSION = 24
STAT_ABORT = 25

# ---------- COMPUTER VISION CORE ALGORITHM ----------

def profile(fn):
    # A decorator function to determine the run time of functions
    def with_profiling(*args, **kwargs):
        start_time = time.time()
        ret = fn(*args, **kwargs)
        elapsed_time = time.time() - start_time
        info("Time elapsed for function: %s: %.4f"%(fn.__name__, elapsed_time))
        return ret
    return with_profiling

def cropImage(img, exc_up, exc_down, exc_l, exc_r, tgt_w, tgt_h):
    # Refer to design notebook for parameter documentation
    assert(exc_up >= 0 and exc_down >= 0 and exc_l >= 0 and exc_r >= 0)
    assert(exc_up + exc_down < 1 and exc_l + exc_r < 1)
    row, col, ch = img.shape
    x = int(col * exc_l)
    y = int(row * exc_up)
    w = int(col - col * exc_r)
    h = int(row - row * exc_down)
    return cv2.resize(img[y:h, x:w], dsize = (tgt_w, tgt_h))

def grayToRGB(img):
    # Converts grayscale image into RGB
    # This conversion uses numpy array operation and takes less time
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

@profile
def findBlurred(img, blur_factor):
    return cv2.medianBlur(img, int(blur_factor//2*2+1))

def isValidPt(img, x, y):
    # Determines if pt lies in img
    h, w = img.shape[0], img.shape[1]
    return (0 <= x and x < w) and (0 <= y and y < h)

def _isPotentialTrackingPoint(grayimg, pt,
    threshold=180, samplesize=4, certainty=0.7):
    # Using threshold value to identify whether it is a valid point
    # @param:
    # grayimg: (ndarray) the image with one channel: graysacle
    # pt: ([2D]tuple) the point to check
    # threshold: (int) the threshold value in grayscale
    # samplesize: (int) the size of sampling matrix
    # certainty: (float) the saturation of valid points in matrix

    h, w = grayimg.shape[0], grayimg.shape[1]
    cx, cy = pt[0], pt[1] # Center coordinates
    if grayimg[cy, cx] > threshold:
        # The point satisifies threshold, we look at a square near it
        # and increment validcount as we find more valid pixels
        totalcount = samplesize ** 2
        validcount = 0
        for x in xrange(cx - samplesize, cx + samplesize + 1):
            for y in xrange(cy - samplesize, cy + samplesize + 1):
                if isValidPt(grayimg, x, y):
                    # Valid dimensions, index within bounds
                    if grayimg[y, x] > threshold: validcount += 1
                else:
                    totalcount -= 1
        # We have a count of valid points, compare it with threshold count
        if validcount > certainty * totalcount: return True
    return False

def _getTrackingPointProbability(img, pt):
    # This is a PMF (Probability Mass Function) for tracking points
    # @param:
    # img: (ndarray) the image with one channel: graysacle
    # pt: ([2D]tuple) the point to check
    return 1

    h, w = img.shape[0], img.shape[1]
    x, y = pt[0], pt[1]
    concession = 0.1
    return min(1 - ((x-w/2)/w)**2 - ((y-h/2)/h)**2, 1 - concession)

def _getNextTrackingPtProbability(img, pt, prevpt, basis,
    a, b, c):
    # This is a PMF, for next tracking point position
    # @param:
    # img: (ndarray) the image with one channel: grayscale
    # pt: ([2D]tuple) the point to check
    # prevpt: ([2D]tuple) the previous tracking point
    # basis: ([2D]tuple) the origin vector for probabilistic sampling circle
    #   which directs to direction of highest favorability
    # a: (float) the preset probability of alpha region
    # b: (float) the preset probability of beta region
    # c: (float) the preset probability of gamma region
    bx, by = basis[0], basis[1]
    theta0 = math.atan2(by, bx) # -pi < theta <= pi

    dx, dy = pt[0] - prevpt[0], pt[1] - prevpt[1]
    dtheta = abs(math.atan2(dy, dx) - theta0)
    if 0 <= dtheta < math.pi/6:
        return a
    elif math.pi/6 <= dtheta < math.pi/2:
        return b
    elif math.pi/2 <= dtheta < math.pi:
        return c
    else:
        return 0

def _getPointsAroundPoint(pt, radius, basis, step=30):
    # Returns a list of points in a disk around pt
    # @param:
    # pt: ([2D]tuple) the center point
    # radius: (int) the radius of disk
    # basis: ([2D]vector) the direction in which we should look
    # step: (float) the step in radian
    # @returns:
    # list: collection of points in disk
    res = []
    x, y = pt[0], pt[1]
    for i in xrange(0, step):
        theta = 2 * math.pi / step * i
        res.append( (int(x + radius * math.cos(theta)),
            int(y + radius * math.sin(theta))) )
    return res

@profile
def samplePoints(grayimg, isTrackingPt,
     n=5, radius=6, a=0.6, b=0.3, c=0.1,
     threshold=180, samplesize=4, certainty=0.7):
    # @param:
    # grayimg: (nparray) the image we want to process, in grayscale
    # isTrackingPt: (grayimg, pt, threshold, samplesize, certainty) -> bool
    #   A function that determines whether the point is a tracking point or not
    # n: number of points we wish to sample
    # radius: radius of circle within which we want to search for points
    # a: (float) the preset probability of alpha region
    # b: (float) the preset probability of beta region
    # c: (float) the preset probability of gamma region
    # threshold: (int) the threshold value in grayscale
    # samplesize: (int) the size of sampling matrix
    # certainty: (float) the saturation of valid points in matrix

    # Mathematically speaking, n * radius should be less than height of image
    # Test if parameters are valid:
    h, w = grayimg.shape[0], grayimg.shape[1]

    if h / radius - 1 <= n:
        raise ParameterInvalidException("sampling circles exceed maximum")
    if type(grayimg) is not np.ndarray:
        raise ParameterInvalidException("input image not valid ndarray")

    #grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    points = []

    # Main loop driving the sampling process
    basis = [0, 0 - radius]
    for i in xrange(n):
        # i: the index of tracking point
        if i == 0:
            # Base case, we want to find a starting pt to work with
            best = ((w/2, h - radius), 0.1)
            for col in xrange(0, w, radius // 2):
                pt = (col, h - radius)
                if isTrackingPt(grayimg, pt,
                    threshold, samplesize, certainty):
                    p = _getTrackingPointProbability(grayimg, pt)
                    if p > best[1]: best = (pt, p)
            points.append(best[0])
        else:
            assert(len(points) > 0)
            # Work with previous located pt
            prevpt = points[-1]
            # Predict the next point location. If not found, this is to be
            # default.
            # NOTE: It would be possibly better to increase sampling radius
            # once the previous sampling gave us the less promising result.
            best = ((prevpt[0] + basis[0], prevpt[1] + basis[1]), 0.1)
            for pt in _getPointsAroundPoint(prevpt, radius, basis):
                x, y = pt[0], pt[1]
                if isValidPt(grayimg, x, y) and isTrackingPt(grayimg, pt,
                    threshold, samplesize, certainty):
                    p = _getNextTrackingPtProbability(grayimg, pt, prevpt,
                        basis, a, b, c)
                    if p > best[1]: best = (pt, p)
            points.append(best[0])
            assert(len(points) > 1)
            # Update basis
            basis[0] = points[-1][0] - points[-2][0]
            basis[1] = points[-1][1] - points[-2][1]
    return points

@profile
def sampleContourArray(img, interval=12, injective=False):
    #TODO: This function has malfunctioning x, y correspondance.
    h = img.shape[0]
    w = img.shape[1]
    # We sample the processed, contour image to produce a set
    # of points for bezier curve approximation
    # Here we sample the image with interval of size of stroke = 3

    # List for data point storage
    P = []
    points = {}
    for x in xrange(w-1):
        for y in reversed(xrange(h-1)):
            if x % interval == 0 and y % interval == 0:
                pixel = img[y, x]
                if pixel[0] == 0 and pixel[1] == 255 and pixel[2] == 0:
                    if injective:
                        points[x] = y
                    else:
                        P.append((x, y))
    if injective:
        for key in points:
            P.append((key, points[key]))

    P = sorted(P)

    n = len(P)
    # print "points found: %d"%len(P)
    # n = len(P) - 1
    n = n - 1
    # Degree of curve
    k = 4
    # property of b-splines: m = n + k + 1
    m = n + k + 1
    # t between clamped ends will be evenly spaced
    _t = 1.0 / (m - k * 2)
    # clamp ends and get the t between them
    t = k * [0] + [t_ * _t for t_ in xrange(m - (k * 2) + 1)] + [1] * k

    # Generate curve. Usage: S(x) -> y
    S = bezier.Bspline(P, t, k)
    #print P
    return S

# ----------------------- END ------------------------
# ------------------ SYS ARGV PARSER -----------------

def captureAndSaveImage():
    # Boot option: -c, captures image with recognition
    stream = io.BytesIO()
    CAMERA.resolution = (V_WIDTH, V_HEIGHT)
    CAMERA.framerate = FRAMERATE
    CAMERA.start_preview()
    time.sleep(0.5)
    CAMERA.capture(stream, format='jpeg')
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    raw_img = cv2.imdecode(data, 0) # Returns a grayscale image
    blurred = findBlurred(raw_img, CV_BLUR_FACTOR)
    display, pointlst = processing.get_good_pts(blurred, raw_img,
        interval=ALPHACV_INTERVAL, pt_count=ALPHACV_PT_COUNT,
        skip=ALPHA_CV_ROW_SKIP, choose_thin=ALPHA_CV_CHOOSE_THIN)
    # assert(len(pointlst) == 0): this is postcondition of alphacv
    filename = 'captured/' + time.ctime().replace(' ', '_').replace(':', '_') \
        + '.jpg'
    cv2.imwrite(filename, display)


# Parse the input parameters:
try:
    # --help, --standalone, --mode: 'alpha' or 'beta'
    # h: help; s: standalone; m: either 'alpha' or 'beta'
    opts, args = getopt.getopt(sys.argv[1:], 'hsm:iktc', [])
except getopt.GetoptError:
    print "usage: run 'framework.py -h' to see documentation"
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print 'usage: framework.py (-s (-m <mode> -i -k))'
        print flash
        print '-h           Print help (this message) and exit'
        print '-s           Run standalone mode independent of client'
        print '-i           Invert the color seen (we are tracking white line)'
        print '-m <mode>    Select CV Mode being used'
        print '             -> alpha: new histogram model'
        print '             -> beta: obsolete probabilistic tracking model'
        print '------------------ALPHACV EXCLUSIVE OPTIONS------------------'
        print '-c           Save processed image (under alphacv)'
        print '-k           Row skip: allow skipping rows for grouping'
        print '-t           Choose thin: whether we shall favor thinner group'
        sys.exit(2)
    elif opt in ('-s', '--standalone'):
        STANDALONE = True

    elif opt in ('-m', '--mode'):
        if arg == 'alpha':
            init('system running on alpha histogram algorithm.')
            CV_MANUAL_MODE = 'alpha'
        elif arg == 'beta':
            init('system running on beta probabilistic algorithm.')
            CV_MANUAL_MODE = 'beta'
        else:
            warn('not a valid mode, falling back to alpha.')
            CV_MANUAL_MODE = 'alpha'

    elif opt in ('-i', '--inverted'):
        info('inverted cam mode enabled.')
        CV_MANUAL_IRNV = True

    elif opt in ('-k',):
        info('row skipping enabled.')
        ALPHA_CV_ROW_SKIP = True

    elif opt in ('-t',):
        info('choose_thin enabled.')
        ALPHA_CV_CHOOSE_THIN = True

    elif opt in ('-c',):
        info('capturing image with alphacv, please wait until program exits.')
        captureAndSaveImage()
        info('succeeded, exiting.')
        sys.exit(0)

    else:
        warn('unhandled option, cowardly exiting.')
        sys.exit(2)

# Clean namespace
try:
    del opts, args
except:
    pass

# ----------------------- END ------------------------

def debugConnection(sock, addr, port):
    # Prints the details of a connection
    warn("connection timed out, plesae check listener status")
    info("detailed Report:")
    info("IP_ADDR: "%addr)
    info("PORT: "%port)
    if not sock.gettimeout(): return
    info("connection timed out after %.3f seconds"%sock.gettimeout())

def startVideoStream_H264(port, stop_event):
    info("setting up streaming socket")
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(0)

    # Make a file-like object out of the connection
    CAMERA.resolution = (V_WIDTH, V_HEIGHT)
    CAMERA.framerate = FRAMERATE
    CAMERA.start_preview()
    time.sleep(0.2)

    connection = server_socket.accept()[0].makefile('wb')
    info("connected to %s for video feed"%(str(server_socket.getpeername())))
    try:
        CAMERA.start_recording(connection, format='h264')
        while not stop_event.is_set():
            pass
        CAMERA.stop_recording()
    finally:
        connection.close()
        server_socket.close()

class ImageProcessor(threading.Thread):
    # An image processor class that does the processing upon frame ready
    def __init__(self, master):
        super(ImageProcessor, self).__init__()
        self.master = master
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.start()

    @profile
    def betacv(self, img):
        master = self.master
        BLUR_FACTOR = master.values['BLUR']
        TRACK_PT_NUM = master.values['PTS']
        RADIUS = master.values['RADI']
        ALPHA = master.values['A']
        BETA = master.values['B']
        GAMMA = 1 - ALPHA - BETA
        THRESHOLD = master.values['THRS']
        SAMPLESIZE = master.values['SIZE']
        CERTAINTY = master.values['CERT']
        # Do the image processing
        # Generate grayscale image
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Blur image
        blurred = findBlurred(grayimg, BLUR_FACTOR)

        # Find dynamic threshold for image
        DYN_THRESHOLD = processing.new_get_gray(blurred, row = V_HEIGHT - 1)

        # Display necessary information on HUD
        cv2.putText(grayimg, "THRESHOLD: %d"%DYN_THRESHOLD, (5, 5),
            cv2.FONT_HERSHEY_SIMPLEX, 12, (0, 255, 0))

        # Grayscale image is faster to fetch for client
        # Update server frame
        master.cntframe = grayimg

        # Find tracking points
        master.trackingpts = samplePoints(blurred, _isPotentialTrackingPoint,
            n=TRACK_PT_NUM, radius=RADIUS, a=ALPHA, b=BETA, c=GAMMA,
            threshold=DYN_THRESHOLD, samplesize=SAMPLESIZE, certainty=CERTAINTY)

        # info(str(master.trackingpts))

    @profile
    def alphacv(self, img):
        # This is an alternative computer vision algorithm proposed by Matthew
        master = self.master
        BLUR_FACTOR = master.values['BLUR']
        TRACK_PT_NUM = master.values['PTS']
        RADIUS = master.values['RADI']
        ALPHA = master.values['A']
        BETA = master.values['B']
        GAMMA = 1 - ALPHA - BETA
        THRESHOLD = master.values['THRS']
        SAMPLESIZE = master.values['SIZE']
        CERTAINTY = master.values['CERT']
        # Do the image processing
        # Generate grayscale image
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Blur image
        blurred = findBlurred(grayimg, BLUR_FACTOR)

        # The dynamic threshold calculation is embedded in algorithm
        # TODO: Experiment to be done to determine the realibility of statistic

        # Display necessary information on HUD

        # Find tracking segments
        interval = ALPHACV_INTERVAL
        pt_count = ALPHACV_PT_COUNT #min(TRACK_PT_NUM, interval)
        # grayimg, pts = processing.get_good_pts(blurred, grayimg,
            # interval = interval, pt_count = pt_count,
            # skip=ALPHA_CV_ROW_SKIP, choose_thin=ALPHA_CV_CHOOSE_THIN)

        grayimg, pts = processing.get_tracking_data(blurred, grayimg,
            master.loopstate,
            interval = interval, pt_count = pt_count,
            skip=ALPHA_CV_ROW_SKIP, choose_thin=ALPHA_CV_CHOOSE_THIN,
            split_detection = True)

        master.cntframe = grayimg
        master.trackingpts = pts

    def run(self):
        # Runs as separate thread
        # If you want to terminate the stream generator set
        # self.master.done = True
        while not self.terminated:
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
                    # Do the image processing
                    img = Image.open(self.stream).convert('RGB')
                    img = np.array(img)
                    img = img[:, :, ::-1].copy()

                    if self.master.filterstate == 3:
                        # IRNV: invert color
                        img = cv2.bitwise_not(img)
                        self.betacv(img)

                    elif self.master.filterstate == 4:
                        img = cropImage(img, VERT_EXC_UP, VERT_EXC_DOWN,
                            HORI_EXC_L, HORI_EXC_R,
                            tgt_w = V_WIDTH, tgt_h = V_HEIGHT)
                        self.alphacv(img)

                    elif self.master.filterstate == 6:
                        # HYBRID
                        # IRNV + ALPHACV
                        img = cv2.bitwise_not(img)
                        self.alphacv(img)

                    else:
                        self.betacv(img)

                except Exception as inst:
                    echoException()
                    warn("image processor exception, frame skipped")

                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return to pool for next frame
                    with self.master.lock:
                        self.master.pool.append(self)

class MobotFramework(object):
    def __init__(self):
        # Note: This class utilizes pre-coded parameters
        # This class does not have the ability to interact with client
        # Core framework
        init('mobot basic framework initiating...')
        self.uptime = time.time()
        self.missionuptime = time.time()

        self.filterstate = 0

        self.values = {
            'BRIG': 0, 'CNST': 50, 'BLUR': CV_BLUR_FACTOR,
            'THRS': 150, 'SIZE': 3, 'CERT': 0.7, 'PTS': 4, 'RADI': 30,
                'A': 0.6, 'B': 0.3, 'C': 0.1,
            'TCHS': 0.5, 'GATG': 14, 'MAXS': 100
        }

        self.status = {
            'STAT': STAT_ONLINE, 'ACTT': 0, 'MIST': 0, 'DELY': 0,
            'GATC': 0, 'SPED': 0, 'PROT': 0, 'CVST': STAT_ONLINE,
            'BATT': 100, 'ADDR': LOCAL_ADDR
        }

        self.emptyfootage = np.zeros((V_HEIGHT, V_WIDTH), dtype = np.uint8)
        self.cntframe = self.emptyfootage
        self.trackingpts = []

        self.vL = 0 # left speed
        self.vR = 0 # right speed
        self.encL = 0 # left encoder
        self.encR = 0 # right encoder

        self.touchcount = 0

        # Main EV3 control threads
        self.loopstop = threading.Event()
        self.loopthd = threading.Thread(target=self.mainloop,
            args=(self.loopstop,))
        self.loopthd.daemon = True

        self.hardwarestop = threading.Event()
        self.hardwarethd = threading.Thread(target=self.update,
            args=(self.hardwarestop,))
        self.hardwarethd.daemon = True

        # Remote video streaming therad
        # self.videostop = threading.Event()
        # self.videothd = None

        # Enable camera
        self.stream = io.BytesIO()
        init("enabling camera")
        CAMERA.resolution = (V_WIDTH, V_HEIGHT)
        CAMERA.framerate = FRAMERATE
        CAMERA.start_preview()
        time.sleep(0.2)
        # CAMERA.capture_continuous(self.stream, format='jpeg')

        # Image Processor Control Variables
        self.done = False # stops Image Processor
        self.lock = threading.Lock()
        self.pool = [] # Pool of Image Processors

        # PID Control Variable
        self.basespeed = MOTOR_BASESPEED
        self.errorsum = 0
        self.preverr = 0
        self.p = CTRL_P
        self.i = CTRL_I
        self.d = CTRL_D

        # Variable that stores inclination button state
        self.incline_btn_prev = False

        # Loop control state machine
        self.loopstate = processing.BifurcationState(V_WIDTH, V_HEIGHT,
            LOOP_CHOICES)

    @staticmethod
    def yieldstreams(scv):
        # This is a generator that gives stream to image processors
        while not scv.done:
            with scv.lock:
                if scv.pool:
                    processor = scv.pool.pop()
                else:
                    processor = None
            if processor:
                yield processor.stream
                processor.event.set()
            else:
                # Pool is starved, wait for it to refill
                time.sleep(0.1)

    def _updateStatus(self):
        # Polls device information and updates status dict
        self.status['STAT'] = STAT_ONLINE
        self.status['ACTT'] = int(time.time() - self.uptime)
        self.status['MIST'] = 0
        self.status['DELY'] = 100
        self.status['CVST'] = STAT_ONLINE
        self.status['BATT'] = 99
        self.status['SPED'] = self._calcMobotSpeed()

    def _setMotorSpeed(self, l, r):
        if abs(l) > 255 or abs(r) > 255:
            raise ParameterInvalidException("Invalid motor speeds")
        self.vL = int(l); self.vR = int(r)
        # BrickPi.MotorSpeed[L] = l
        # BrickPi.MotorSpeed[R] = r

    def _calcMobotSpeed(self):
        # Calculates speed of robot relatively
        return int((self.vL + self.vR) / 2.0)

    def mainloop(self, stop_event):
        BUFFERSIZE = 4
        self.pool = [ImageProcessor(self) for i in xrange(BUFFERSIZE)]
        CAMERA.capture_sequence(MobotFramework.yieldstreams(self),
            use_video_port=True)

    def setInclined(self):
        info('set inclined!')
        self.p = RAMP_P
        self.i = RAMP_I
        self.d = RAMP_D
        self.basespeed = RAMP_BASESPEED

    def unsetInclined(self):
        info('unset inclined!')
        self.p = CTRL_P
        self.i = CTRL_I
        self.d = CTRL_D
        self.basespeed = MOTOR_BASESPEED

    def update(self, stop_event):
        # Mobot hardware update loop
        # self.alphacv() # Removed: Image Processing doesnt happen here anymore
        while not stop_event.is_set():
            self.touchcount = abs(self.touchcount - 1)
            BrickPi.MotorSpeed[L] = self.vL
            BrickPi.MotorSpeed[L1] = self.vL
            BrickPi.MotorSpeed[R] = self.vR
            BrickPi.MotorSpeed[R1] = self.vR
            result = BrickPiUpdateValues()
            if not result:
                # Successfully updated values
                # Read touch sensor values
                if BrickPi.Sensor[S2]:
                    # Prevent signal disturbances
                    threshold = int(28 - self.values['TCHS'] * 20)
                    self.touchcount += 2
                    if self.touchcount > threshold:
                        # Increment gates count
                        self.status['GATC'] += 1
                        # Reset signal strength
                        self.touchcount = 0
                # Update encoder values
                self.encL = BrickPi.Encoder[L]
                self.encR = BrickPi.Encoder[R]

            speeds = self.calculateMobotMovement()
            self._setMotorSpeed(speeds[0], speeds[1])
            self._updateStatus()

            # Emergency Abort
            if (not GPIO.input(ABORT_BTN)):
                warn('manually aborting mission!!!')
                self.stopMission()
                CAMERA.close()
                sys.exit(0)

            # Ramp Adapatation
            incline_btn = not GPIO.input(RAMP_BTN)
            if ((not self.incline_btn_prev) and incline_btn):
                # Button is pressed, set inclined
                self.setInclined()

            elif ((self.incline_btn_prev) and not incline_btn):
                # Button is released, unset inclined
                self.unsetInclined()

            self.incline_btn_prev = incline_btn

            # Update Terminal Feedback
            # Should be disabled for safety considerations -> STABLE_MODE
            if term2 != None and not STABLE_MODE:
                c = term2.scr.getch()
                if c == 410:
                    info("@terminal: resize event")
                    term2.resizeAll()
                term2.refreshAll()

    def startMission(self, join=False):
        # Warning: join in to be enabled for standalone version
        # because no main thread would be present
        info('mission started')
        self.loopstop.clear()
        self.hardwarestop.clear()
        self.done = False
        self.loopthd.start()
        if join:
            try:
                self.hardwarethd.start()
                self.hardwarethd.join()
            except KeyboardInterrupt:
                self.stopMission()
        else:
            self.hardwarethd.start()

    def stopMission(self):
        info('mission exited')
        self.done = True
        self.loopstop.set()
        self.hardwarestop.set()
        # Shut down the processors orderly
        while self.pool:
            with self.lock:
                processor = self.pool.pop()
            processor.terminated = True
            # Suspicious join method
            # processor.join()

    def setFilterState(self, state):
        # Manually sets the filter state, ususally called by standalone wrapper
        if type(state) is not int: return
        self.filterstate = state

    def calculateMobotMovement(self):
        # return (0,0)
        # Error is the offset of the bottom trackpoint from middle of frame
        if len(self.trackingpts) == 0: return (0, 0)
        err = self.trackingpts[0][0] - V_WIDTH / 2

        # Proportion term
        pterm = err * self.p
        # Calculate the integral term
        self.errorsum += err
        iterm = self.errorsum * self.i
        # Calculate the derivative term
        dterm = (err - self.preverr) * self.d
        self.preverr = err
        # Drive is the difference in speed between two wheels
        # Drive is positive when turning left
        drive = int(pterm + iterm + dterm)

        lwheel = -(self.basespeed + drive)
        rwheel = -(self.basespeed - drive)

        # Cap the wheel speeds to [-255, 255]
        lwheel = min(max(lwheel, -255), 100)
        rwheel = min(max(rwheel, -255), 100)

        return (lwheel, rwheel)

class MobotService(rpyc.Service, MobotFramework):
    def __init__(self, *args, **kwargs):
        # Inherit from basic framework
        MobotFramework.__init__(self)
        rpyc.Service.__init__(self, *args, **kwargs)
        init("mobot service instance created")

        # Status
        self._connected = False

        # Remote video streaming therad
        self.videostop = threading.Event()
        self.videothd = None

    def on_connect(self):
        info("received connection")
        self._connected = True
        self.startMission()

    def on_disconnect(self):
        warn("connection lost")
        self._connected = False
        self.stopMission()

    def exposed_recognized(self):
        return True

    def exposed_setFilterState(self, state):
        self.setFilterState(state)

    def exposed_getMobotStatus(self):
        # Returning the weak reference to states dict
        # Changing the values in dict will directly affect local var
        return self.status

    def exposed_getMobotValues(self):
        # Returning the weak reference to values dict
        # Changing the values in dict will directly affect local var
        return self.values

    def exposed_getVideoSpecs(self):
        # Returns the frame size
        return (V_WIDTH, V_HEIGHT)

    def exposed_getCurrentFrame(self):
        # Returns a string of ndarray in grayscale
        return self.cntframe.tostring()

    def exposed_getTrackingPts(self):
        return self.trackingpts

    # Not suggested but usable: drags down performance dramatically
    def exposed_startVideoStream(self, port):
        # Establishs a TCP connection with interface for video streaming
        if self.videothd != None:
            warn("video streaming already running")
            return
        self.videothd = threading.Thread(target=startVideoStream_H264,
            args=(port, self.videostop))
        self.videothd.daemon = True
        info("starting video stream")
        self.videothd.start()

    def exposed_stopVideoStream(self):
        info("stopping video stream")
        self.videostop.set()

    def exposed_setMotorSpeed(self, l, r):
        maxspeed = self.values['MAXS']
        l = l * (maxspeed / 255.0)
        r = r * (maxspeed / 255.0)
        self._setMotorSpeed(l, r)

if __name__ == "__main__":
    if not STANDALONE:
        init('interactive mode enabled by default')
        init('initiating mobot server')
        server = ThreadedServer(MobotService, port = MOBOT_PORT)
        server.start()

    else:
        init('standalone mode')
        init('creating offline worker instance')
        f_state = 4 # Default value
        if CV_MANUAL_MODE == 'alpha':
            if not CV_MANUAL_IRNV:
                f_state = 4
            else:
                f_state = 6
        elif CV_MANUAL_MODE == 'beta':
            if not CV_MANUAL_IRNV:
                f_state = 0
            else:
                f_state = 3
        else:
            warn('internal error: wrong CV_MANUAL_MODE entry')
            info('falling back to alpha, non-inverted mode')
            f_state = 4

        # Initialize offline instance
        mobot = MobotFramework()
        mobot.setFilterState(f_state)
        mobot.startMission(join=True)
        # An offline version will not terminate
        # TODO: add state machine to tackle loops, and terminate the movement
        CAMERA.close()
