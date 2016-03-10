##################################
# Mobot Algorithm Design Panel   #
# copyright 2015-2016 Harvey Shi #
##################################
flash = \
"""
  __  .__                       _____.__                .__
_/  |_|  |__   ____           _/ ____\  | _____    _____|  |__
\   __\  |  \_/ __ \   ______ \   __\|  | \__  \  /  ___/  |  \\
 |  | |   Y  \  ___/  /_____/  |  |  |  |__/ __ \_\___ \|   Y  \\
 |__| |___|  /\___  >          |__|  |____(____  /____  >___|  /
           \/     \/                           \/     \/     \/
"""
import cv2
import time
import rpyc
import logging
import copy
import Tkinter as tk
import numpy as np
import bezier
import math
import itertools
from PIL import Image, ImageTk

import UI_Mobot_Configuration as ui

class ParameterInvalidException(Exception):
    def __init__(self, description):
        self.des = description

    def __str__(self):
        return repr(self.des)

def profile(fn):
    # A decorator function to determine the run time of functions
    def with_profiling(*args, **kwargs):
        start_time = time.time()
        ret = fn(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print "Time elapsed for function: %s: %.4f"%(fn.__name__, elapsed_time)
        return ret
    return with_profiling

ex_img = cv2.imread('../tests/1.JPG',0)

HEIGHT, WIDTH = ex_img.shape
ex_img = cv2.resize(ex_img, dsize=(WIDTH//20, HEIGHT//20))
blurred = cv2.medianBlur(ex_img, 5)
#blurred = cv2.GaussianBlur(ex_img, (5,5), 0)
edges = cv2.Canny(blurred,0,500)

def grayToRGB(img):
    # Converts grayscale image into RGB
    # This conversion uses numpy array operation and takes less time
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # By accessing pixel arrays:
    # splited = cv2.split(image)
    # B = splited[:,0]
    # G = splited[:,1]
    # R = splited[:,2]
    # Merged = cv2.merge((R, G, B))

def rgbToTkImage(img):
    im = Image.fromarray(img)
    return ImageTk.PhotoImage(im)

def grayToTkImage(img):
    # Convert the Image object into a TkPhoto object
    im = Image.fromarray(grayToRGB(img))
    return ImageTk.PhotoImage(im)

@profile
def findEdges(img, blur_factor, edge_low, edge_high):
    blurred = cv2.medianBlur(img, int(blur_factor//2*2+1))
    edges = cv2.Canny(blurred, edge_low, edge_high)
    return edges

@profile
def findBlurred(img, blur_factor):
    return cv2.medianBlur(img, int(blur_factor//2*2+1))

@profile
def findContours(img):
    major_ver, minor_ver, subminor_ver = (cv2.__version__).split('.')
    if int(major_ver) < 3:
        contours = cv2.findContours(img,cv2.RETR_TREE,
                                    cv2.CHAIN_APPROX_SIMPLE)[0]
    else:
        contours = cv2.findContours(img,cv2.RETR_TREE,
                                    cv2.CHAIN_APPROX_SIMPLE)[1]
    return contours

@profile
def findPolys(contours, epsilon=3, closed=False):
    polys = []
    for c in contours:
        polys.append(cv2.approxPolyDP(c, epsilon, closed))
    return polys

class VectorEquation():
    # This class defines a vector equation with arc lenth parameterization
    # methods: VectorEquation.getDerivativeAt(s=0) -> Vector quantity
    pass

def getMobotStatus():
    # Use rpyc to get state of mobot
    # -------STRUCT------
    # SPEED: (Int, Int), BATT: Int,
    # INTEGRITY: Int, CAMERA_ENABLED: Bool,
    # FPS: Int, CPU: Int, CAMERA_MOUNT_ANGLE: Int
    # CAMERA_X_OFFSET: Int, CAMERA_Y_OFFSET: Int
    # -------------------- more to come.
    pass

def isValidPt(img, x, y):
    h, w = img.shape[0], img.shape[1]
    return (0 <= x and x < w) and (0 <= y and y < h)

def _isPotentialTrackingPoint(grayimg, pt):
    # Using threshold value to identify whether it is a valid point
    # @param:
    # grayimg: (ndarray) the image with one channel: graysacle
    # pt: ([2D]tuple) the point to check

    threshold = 180 # Example Value
    samplesize = 4 # Look 4 units before and after each dimension
                   # This implies that there are 9 * 9 = 81 validation points
    certainty = 0.7 # Ratio of valid points within sample square

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

def _getPointsAroundPoint(pt, radius, step=200):
    # Returns a list of points in a disk around pt
    # @param:
    # pt: ([2D]tuple) the center point
    # radius: (int) the radius of disk
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
     n=5, radius=6, a=0.6, b=0.3, c=0.1):
    # @param:
    # grayimg: (nparray) the image we want to process, in grayscale
    # isTrackingPt: (grayimg, pt) -> bool
    #   A function that determines whether the point is a tracking point or not
    # n: number of points we wish to sample
    # radius: radius of circle within which we want to search for points
    # a: (float) the preset probability of alpha region
    # b: (float) the preset probability of beta region
    # c: (float) the preset probability of gamma region

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
    basis = [0, -1]
    for i in xrange(n):
        # i: the index of tracking point
        if i == 0:
            # Base case, we want to find a starting pt to work with
            best = ((w/2, h - radius), 0.1)
            for col in xrange(0, w):
                pt = (col, h - radius)
                if isTrackingPt(grayimg, pt):
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
            for pt in _getPointsAroundPoint(prevpt, radius):
                x, y = pt[0], pt[1]
                if isValidPt(grayimg, x, y) and isTrackingPt(grayimg, pt):
                    p = _getNextTrackingPtProbability(grayimg, pt, prevpt,
                        basis, a, b, c)
                    if p > best[1]: best = (pt, p)
            points.append(best[0])
            assert(len(points) > 1)
            # Update basis
            basis[0] = points[-1][0] - points[-2][0]
            basis[1] = points[-1][1] - points[-2][1]
            print best
            print basis
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
    print "points found: %d"%len(P)
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

@profile
def calculateDesiredVelocityVector():
    # Takes in a equation (set) and calculate desired velocity vector
    pass

def convertVelocityVectorToSpeeds():
    # This function converts a velocity vector into L/R speed tuple
    pass

class ConfigurationMainFrame():
    def __init__(self):
        #self.ReceiveDiagnoseBool = tk.StringVar()

        ui.UI_Mobot_Configuration_support.connectAction = \
            self.connectAction
        ui.UI_Mobot_Configuration_support.pingAction = \
            self.pingAction
        ui.UI_Mobot_Configuration_support.settingsChanged = \
            self.settingsChanged
        ui.UI_Mobot_Configuration_support.emergencyStopAction = \
            self.emergencyStopAction

        #ui.UI_Mobot_Configuration_support.ReceiveDiagnoseBool = \
        #    self.ReceiveDiagnoseBool
        self.conn = None

    # UI Methods
    def connectAction(self):
        print "Connect Action"
        HOSTNAME = ui.w.IPEntry.get()
        PORT = int(ui.w.PortEntry.get())
        logging.info("Connecting to client: %s@PORT%d"%(HOSTNAME, PORT))
        try:
            self.conn = rpyc.connect(HOSTNAME, PORT)
        except:
            logging.warn("No valid services found.")
        self.updateMobotInfo()

    def pingAction(self):
        print "Ping Action"

    def settingsChanged(self, e):
        print '{:-^30}'.format("UPDATED SETTINGS")
        print '{:^30}'.format("Blur: %d"%(ui.w.BlurScale.get()))
        print '{:^30}'.format("Canny Lo: %d"%(ui.w.CannyLoScale.get()))
        print '{:^30}'.format("Canny Hi: %d"%(ui.w.CannyHiScale.get()))
        self.updateDashboardImages()
        print '{:-^30}'.format("")

    def emergencyStopAction(self):
        print "Emergency Stop"

    # Framework Methods
    #@profile
    def updateDashboardImages(self):
        #if self.conn == None: return
        BLUR_FACTOR = ui.w.BlurScale.get()
        CANNY_LO = ui.w.CannyLoScale.get()
        CANNY_HI = ui.w.CannyHiScale.get()
        originalImage = ex_img
        #print type(originalImage)
        processedImage = findEdges(originalImage,
            BLUR_FACTOR, CANNY_LO, CANNY_HI)
        #print type(processedImage)
        #print processedImage
        HEIGHT, WIDTH = originalImage.shape
        computerVisionImage = grayToRGB(copy.copy(originalImage))

        contours = findContours(processedImage)
        if ui.UI_Mobot_Configuration_support.LineApproxBool.get() == "1":
            print "Finding Approximate Poly Curves with epsilon = 3"
            contours = findPolys(contours)
            print "Polys found: %d"%len(contours)
        cv2.drawContours(computerVisionImage, contours, -1, (0, 255, 0), 3)

        blurred = findBlurred(originalImage, BLUR_FACTOR)
        trackpts = samplePoints(blurred, _isPotentialTrackingPoint,
            n=5, radius=20)
        print 'tracking points found:'
        print trackpts

        blurred = grayToRGB(blurred)
        for pt in trackpts:
            cv2.circle(blurred, pt, 2, (255, 0, 0))

        """
        # Now we have an image where contours are detected
        # We sample the transformed image and try to use Bezier
        # Approximation to deduce a continous differentiable curve.
        S = sampleContourArray(computerVisionImage)

        # The curve is supposed to be used for mathematical evaluation
        # algorithm that determines how the robot should move.
        # Since this is a preview configuration algorithm, we are only
        # doing previews with it.
        w = computerVisionImage.shape[1]
        STEP_N = 1000
        STEP_SIZE = float(1) / STEP_N
        for x in xrange(STEP_N):
            t_ = x * STEP_SIZE
            try:
                x, y = S(t_)
                computerVisionImage[int(y), int(x)] = [255, 0, 0]
                #print "SUCCESS POINT, x = %d"%x
            except:
                pass
        """
        # Convert To Tkinter images, should not be timed.
        originalImage = grayToTkImage(originalImage)
        processedImage = rgbToTkImage(blurred)
        computerVisionImage = rgbToTkImage(computerVisionImage)

        ui.w.OriginalImageLabel.configure(image = originalImage)
        ui.w.OriginalImageLabel.image = originalImage
        ui.w.ProcessedImageLabel.configure(image = processedImage)
        ui.w.ProcessedImageLabel.image = processedImage
        """
        ui.w.CVImageLabel.configure(image = computerVisionImage)
        ui.w.CVImageLabel.image = computerVisionImage
        """

    def updateMobotInfo(self):
        if self.conn == None: return
        batt = self.conn.root.getBattery()
        ui.w.TProgressbar1.step(amount=abs(batt-1))
        ui.w.Label9.config(text=str(batt))

if __name__ == "__main__":
    print flash
    MainFrame = ConfigurationMainFrame()
    ui.vp_start_gui()
