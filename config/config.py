import cv2
import time
import rpyc
import logging
import copy
import Tkinter as tk
import numpy as np
from PIL import Image, ImageTk

import UI_Mobot_Configuration as ui

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

WIDTH, HEIGHT = ex_img.shape
ex_img = cv2.resize(ex_img, dsize=(WIDTH//16, HEIGHT//16))
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
def findContours(img):
    contours = cv2.findContours(img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[0]
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
            contours = polys = findPolys(contours)
            print "Polys found: %d"%len(contours)
        cv2.drawContours(computerVisionImage, contours, -1, (0, 255, 0), 3)

        # Convert To Tkinter images, should not be timed.
        originalImage = grayToTkImage(originalImage)
        processedImage = grayToTkImage(processedImage)
        computerVisionImage = rgbToTkImage(computerVisionImage)

        ui.w.OriginalImageLabel.configure(image = originalImage)
        ui.w.OriginalImageLabel.image = originalImage
        ui.w.ProcessedImageLabel.configure(image = processedImage)
        ui.w.ProcessedImageLabel.image = processedImage
        ui.w.CVImageLabel.configure(image = computerVisionImage)
        ui.w.CVImageLabel.image = computerVisionImage

    def updateMobotInfo(self):
        if self.conn == None: return
        batt = self.conn.root.getBattery()
        ui.w.TProgressbar1.step(amount=abs(batt-1))
        ui.w.Label9.config(text=str(batt))

if __name__ == "__main__":
    MainFrame = ConfigurationMainFrame()
    ui.vp_start_gui()
