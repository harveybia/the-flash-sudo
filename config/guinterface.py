################################
#   Mobot Operation Interface  #
# copyright 2015-2016 Elias Lu #
################################

import string
import math
import random
import os
import time
import rpyc
import socket
import subprocess
import numpy as np
from Tkinter import *
from PIL import Image, ImageTk

MOBOT_ADDR = "128.237.177.201"
MOBOT_PORT = 15112
VIDEO_PORT = 20000
ADDR, PORT = 'localhost', 15251
# Video Configuration
V_WIDTH, V_HEIGHT = 320, 240

newaddr = raw_input("Backbone server adderss, leave empty for localhost: ")
if newaddr != "": ADDR = newaddr
newport = raw_input("Port number, leave empty for 15251: ")
if newport != "": ADDR = int(newaddr)
del newaddr, newport

# For Unit Test Purposes
import cv2

def _grayToRGB(img):
    # Converts grayscale image into RGB
    # This conversion uses numpy array operation and takes less time
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

def _rgbToTkImage(img):
    im = Image.fromarray(img)
    return ImageTk.PhotoImage(im)

def _grayToTkImage(img):
    # Convert the Image object into a TkPhoto object
    im = Image.fromarray(_grayToRGB(img))
    return ImageTk.PhotoImage(im)

def startVideoStream(addr=MOBOT_ADDR, port=VIDEO_PORT):
    return cv2.VideoCapture(0)
    #client_socket = socket.socket()
    #client_socket.connect((addr, port))
    #stream = client_socket.makefile('rb')
    #return stream

def readTkImage(stream):
    ret, frame = stream.read()
    if ret:
        resized = cv2.resize(frame, dsize=(V_WIDTH, V_HEIGHT))
        return _rgbToTkImage(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
    else:
        return ImageTk.PhotoImage('RGB', (V_WIDTH, V_HEIGHT))

# turn int value to str #
def interpretKeyValue(statusDic):
    for key in statusDic:
        if statusDic[key] == 22:
            statusDic[key] = "ONLINE"
        elif statusDic[key] == 23:
            statusDic[key] = "DISCONNECTED"
        elif statusDic[key] == 24:
            statusDic[key] = "IN MISSION"
        elif statusDic[key] == 25:
            statusDic[key] = "ABORT"
    return statusDic

def addUnit(statusDic):
    for key in statusDic:
        if key == "ACTT" or key == "MIST" or key == "PROT":
            if statusDic[key] == 0:
                statusDic[key] = str(statusDic[key]) + " SECOND"
            else: statusDic[key] = str(statusDic[key]) + " SECONDS"
        elif key == "DELY":
            statusDic[key] = str(statusDic[key]) + " MS"
        elif key == "SPED":
            statusDic[key] = str(statusDic[key]) + " MS^-1"
        elif key == "GATC":
            if statusDic[key] == 0:
                statusDic[key] = str(statusDic[key]) + " GATE PASSED"
            else: statusDic[key] = str(statusDic[key]) + " GATES PASSED"
    return statusDic


# Colors
FrameBG = "#2B3990"
ButtonBG = "#1C75BC"
Slider1 = "#39B54A"
Slider2 = "#2BB673"
Slider3 = "#00A79D"
EmptyGray = "gray30"

class Application(object):
    # Override these methods when creating your own animation
    def __init__(self): pass
    def mousePressed(self, event): pass
    def keyPressed(self, event): pass
    def timerFired(self): pass
    def redrawAll(self): pass
    def mouseMotion(self, event): pass
    def mouseReleased(self, event): pass

    # Call app.run(width,height) to get your app started
    def run(self, width=1400, height=700):
        # create the root and the canvas
        root = Tk()
        self.width = width
        self.height = height
        self.canvas = Canvas(root, width=width, height=height)
        self.canvas.pack()

        # set up events
        def redrawAllWrapper():
            self.canvas.delete(ALL)
            self.redrawAll()
            self.canvas.update()

        def mousePressedWrapper(event):
            self.mousePressed(event)
            redrawAllWrapper()

        def mouseMotionWrapper(event):
            self.mouseMotion(event)
            redrawAllWrapper()

        def doubleClickedWrapper(event):
            self.doubleClicked(event)
            redrawAllWrapper()

        def mouseReleasedWrapper(event):
            self.mouseReleased(event)
            redrawAllWrapper()

        def keyPressedWrapper(event):
            self.keyPressed(event)
            redrawAllWrapper()

        root.bind("<Button-1>", mousePressedWrapper)
        root.bind("<Motion>", mouseMotionWrapper)
        root.bind("<ButtonRelease>", mouseReleasedWrapper)
        # root.bind("<Double-Button-1>", doubleClickedWrapper)
        root.bind("<Key>", keyPressedWrapper)

        # set up timerFired events
        self.timerFiredDelay = 10 # milliseconds
        def timerFiredWrapper():
            self.timerFired()
            redrawAllWrapper()
            # pause, then call timerFired again
            self.canvas.after(self.timerFiredDelay, timerFiredWrapper)

        # init and get timerFired running
        #self.__init__()
        timerFiredWrapper()
        # and launch the app
        root.mainloop()
        print("Bye")



###############
# Draw Canvas #
###############

class Interface(Application):
    def __init__(self):
        Application.__init__(self)
        self.monitorList = self.getMonitorSelectorList()
        self.missionList = self.getMissionPanelList()
        self.visualList = self.getVisualCtrlList()
        self.parameterList = self.getParameterList()
        self.funcList = self.getFunctionalityList()
        self.hoverList = [False] * 16
        self.chosenList = [True] + [False] * 7 + [True] + [False] * 7
        self.sliderList = [False] * 14
        self.valueList = [0] * 14
        self.startRun = False
        self.unitAdded = False
        status = dict()

        # Connection to backbone server
        self.conn = rpyc.connect(ADDR, PORT)

        # Connection to raw video stream
        self.conn.root.startStream(MOBOT_ADDR, MOBOT_PORT)
        time.sleep(0.5)
        # self.video = startVideoStream()
        # self.image = readTkImage(self.video)

    def getMonitorSelectorList(self):
        return ["ORIG", "PROC", "B/W", "IRNV",
                "CV",   "PRED", "HYBRID", "BLUR"]

    def getMissionPanelList(self):
        return ["IDLE",  "DEBUG",  "LINE TRACE", "RUN",
                "RESET", "CAMERA", "TEST", "ABORT"]

    def getVisualCtrlList(self):
        return ["BRIGHTNESS", "CONTRAST", "BLUR INDEX",
               "-EMPTY-", "-EMPTY-"]

    def getParameterList(self):
        return ["THRESHOLD", 'MAT SIZE', 'MAT SATUR', 'PTS', 'RADIUS',
                'ALPHA', 'BETA', 'GAMMA']

    def getFunctionalityList(self):
        return ['TOUCH SEN', 'GATES TGT', 'MAX SPEED', 'BATTERY', '-EMPTY-']

    def mousePressed(self, event):
        x = event.x
        y = event.y
        ###########
        # buttons #
        ###########
        x0 = 42
        x1 = 418
        y0 = 470
        y1 = 530
        y2 = 590
        y3 = 650
        # for reset button #
        if self.hoverList[12] == True:
            self.chosenList[12] = True
            return # to finalize the board
        # for abort #
        elif self.hoverList[15] == True:
            # stop running
            self.chosenList[11] = False
            self.startRun = False

            self.chosenList[15] = True
            return
        # for run #
        elif self.hoverList[11] == True:
            self.chosenList[11] = True
            self.startRun = True
        # pressing other buttons #
        elif x0<=x<x1 and y0<=y<y1:
            for i in xrange(8):
                if self.hoverList[i] == True:
                    self.chosenList[i] = True
                else: self.chosenList[i] = False
        elif x0<=x<x1 and y2<=y<y3:
            for j in xrange(8, 16):
                if self.hoverList[j] == True:
                    self.chosenList[j] = True
                    # pressing other buttons also terminates running
                    self.chosenList[11] = False
                    self.startRun = False
                else: self.chosenList[j] = False

        ###########
        # sliders #
        ###########
        dW = 10/2
        dH = 22/2
        for i in range(3):
            x0 = 560 + self.valueList[i]*3 - dW
            x1 = 560 + self.valueList[i]*3 + dW
            y0 = 120 + i*40 - dH
            y1 = 120 + i*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sliderList[i] = True
            else: self.sliderList[i] = False

        for j in range(8):
            x0 = 560 + self.valueList[j+3]*3 - dW
            x1 = 560 + self.valueList[j+3]*3 + dW
            y0 = 380 + j*40 - dH
            y1 = 380 + j*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sliderList[j+3] = True
            else: self.sliderList[j+3] = False

        for k in range(3):
            x0 = 1040 + self.valueList[k+11]*3 - dW
            x1 = 1040 + self.valueList[k+11]*3 + dW
            y0 = 120 + k*40 - dH
            y1 = 120 + k*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sliderList[k+11] = True
            else: self.sliderList[k+11] = False



    def mouseMotion(self, event):
        x = event.x
        y = event.y

        # MONITOR #
        for i in xrange(8):
            x0 = 42+94*(i%4)
            x1 = 42+94*(i%4+1)
            y0 = 470+30*(i/4)
            y1 = 470+30*(i/4+1)
            if x0<=x<x1 and y0<=y<y1:
                self.hoverList[i] = True
            else: self.hoverList[i] = False

        # MISSION #
        for i in xrange(8):
            x0 = 42+94*(i%4)
            x1 = 42+94*(i%4+1)
            y0 = 590+30*(i/4)
            y1 = 590+30*(i/4+1)
            if x0<=x<x1 and y0<=y<y1:
                self.hoverList[i+8] = True
            else: self.hoverList[i+8] = False

        # SLIDERS #
        for i in range(3):
            if self.sliderList[i]:
                if x >= 860:
                    newValue = 100
                    self.sliderList[i] = False
                elif x <= 560:
                    newValue = 0
                    if x <= 540:
                        self.sliderList[i] = False
                else: newValue = (x-560)/3
                self.valueList[i] = newValue

        for j in range(3,11):
            if self.sliderList[j]:
                if x >= 860:
                    newValue = 100
                    self.sliderList[j] = False
                elif x <= 560:
                    newValue = 0
                    if x <= 540:
                        self.sliderList[j] = False
                else: newValue = (x-560)/3
                self.valueList[j] = newValue


        for k in range(11,14):
            if self.sliderList[k]:
                if x >= 1340:
                    newValue = 100
                    self.sliderList[k] = False
                elif x <= 1040:
                    newValue = 0
                    if x <= 1020:
                        self.sliderList[k] = False
                else: newValue = (x-1040)/3
                self.valueList[k] = newValue






    def mouseReleased(self, event):
        x = event.x
        y = event.y
        ###########
        # buttons #
        ###########
        x0 = 42
        x1 = 418
        y0 = 470
        y1 = 530
        y2 = 590
        y3 = 650
        # for reset button #
        if self.hoverList[12] == True:
            self.chosenList[12] = False
            self.conn.root.resetStatus()
            return
        # for start button #
        elif self.hoverList[11] == True:
            self.conn.root.startMission()
            return
        # for abort button #
        elif self.hoverList[15] == True:
            self.chosenList[15] = False
            self.conn.root.abortMission()
            return
        # other buttons #
        elif x0<=x<=x1 and y0<=y<=y1:
            for i in xrange(8):
                if self.hoverList[i] == True:
                    self.sendData()
                    return
        elif x0<=x<=x1 and y2<=y<=y3:
            for i in xrange(8, 16):
                if self.hoverList[i] == True:
                    self.sendData()


        ###########
        # sliders #
        ###########
        dW = 10/2
        dH = 22/2
        for i in range(3):
            x0 = 560 + self.valueList[i]*3 - dW
            x1 = 560 + self.valueList[i]*3 + dW
            y0 = 120 + i*40 - dH
            y1 = 120 + i*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sendData()
                self.sliderList[i] = False

        for i in range(8):
            x0 = 560 + self.valueList[i+3]*3 - dW
            x1 = 560 + self.valueList[i+3]*3 + dW
            y0 = 380 + i*40 - dH
            y1 = 380 + i*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sendData()
                self.sliderList[i+3] = False

        for i in range(3):
            x0 = 1040 + self.valueList[i+11]*3 - dW
            x1 = 1040 + self.valueList[i+11]*3 + dW
            y0 = 120 + i*40 - dH
            y1 = 120 + i*40 + dH
            if x0<=x<=x1 and y0<=y<=y1:
                self.sendData()
                self.sliderList[i+11] = False



    def sendData(self):
        filterDic, taskDic, slideDic = self.getData()
        # data transfer protocol
        self.conn.root.updateValues(filterDic, taskDic, slideDic)

    def getData(self):
        FILTER_KEYS   = ['ORIG', 'PROC', 'BW', 'IRNV',
            'CV', 'PRED', 'HYBR', 'BLUR']
        TASK_KEYS   = ['IDLE', 'DEBU', 'TRAC', 'CAM', 'TEST']
        SLIDE_KEYS = [
                      'BRIG', 'CNST', 'BLUR',
                      'THRS', 'SIZE', 'CERT', 'PTS', 'RADI', 'A', 'B', 'C',
                      'TCHS', 'GATG', 'MAXS'
                     ]
        filterDic = dict()
        taskDic = dict()
        slideDic = dict()
        for i in range(8):
            key1 = FILTER_KEYS[i]
            filterDic[key1] = self.chosenList[i]
        for j in range(5):
            key2 = TASK_KEYS[j]
            if j<3:
                taskDic[key2] = self.chosenList[j+8]
            else: taskDic[key2] = self.chosenList[j+10]
        for k in range(14):
            key3 = SLIDE_KEYS[k]
            slideDic[key3] = self.valueList[k]
        return filterDic, taskDic, slideDic


    def keyPressed(self, event):
        pass

    def timerFired(self):
        pass

    def drawBasic(self, canvas):
        canvas.create_rectangle(-5,-5,1405,705,width=0,fill='#262262')
        self.drawCaption(canvas)
        self.drawVideo(canvas)
        self.drawButtons(canvas)
        self.drawSliders(canvas)
        self.drawInfoBar(canvas)

    def drawCaption(self, canvas):
        canvas.create_text(15, 15, anchor=NW, text="THE-FLASH-SUDO",
            font="airborne 24 bold", fill="white")
        canvas.create_text(222,15, anchor=NW, text="MISSION MONITOR",
            font="airborne 24", fill="gray75")
        date = subprocess.check_output(["date"]).decode("utf-8")
        canvas.create_text(23, 45, anchor=NW, text=date,
            font="Airborne-II-Pilot 16", fill="gray85")

    def drawPtStatistics(self, canvas, pt, basis=(0,-1), prob=60):
        canvas.create_oval(pt[0]-2, pt[1]-2, pt[0]+2, pt[1]+2,
            outline="aquamarine")
        canvas.create_text((pt[0]+5, pt[1]), anchor='w', text="%d%%"%prob,
            font=("Airborne", 10), fill='aquamarine')
        canvas.create_line(pt[0], pt[1], pt[0]+basis[0], pt[1]+basis[1],
            fill="red", width=1, arrow=LAST)

    def drawVideo(self, canvas):
        canvas.create_text(30, 90, anchor=NW, text="LIVE FEED",
            font="airborne 18", fill="white")
        # outer canvas
        canvas.create_rectangle(42,119,418,401,fill=ButtonBG,width=0)
        # real video canvas
        canvas.create_rectangle(70,140,390,380,fill=ButtonBG,width=2)
        # draw diagonals
        canvas.create_line(42,119,418,401,width=2)
        canvas.create_line(418,119,42,401,width=2)
        # front view
        canvas.create_text(230,120,anchor=N,text="FRONT",
        font="airborne 16",fill="white")
        # put video on canvas #
        raw = self.conn.root.getMobotVision()
        if raw != None:
            self.image = _grayToTkImage(
                np.fromstring(self.conn.root.getMobotVision(),
                    dtype=np.uint8).reshape((V_HEIGHT, V_WIDTH))
                )
            canvas.create_image(70,140,anchor=NW,image=self.image)


            im = array(Image.open(self.image).convert('L'))
            im2,cdf = imtools.histeq(im)
            canvas.create_image(70,140,anchor=NW,image=im2)

        else:
            # Draw 'No Signal on canvas'
            pass

        # print self.conn.root.getTrackingPts()
        for pt in self.conn.root.getTrackingPts():
            x = pt[0] + 70
            y = pt[1] + 140
            self.drawPtStatistics(canvas, (x, y))

    def drawButtons(self, canvas):
        ####################
        # MONITOR SELECTOR #
        ####################
        canvas.create_text(30,440, anchor=NW, text="MONITOR SELECTOR",
            font="airborne 18", fill="white")
        # draw background color for buttons
        canvas.create_rectangle(42,470,418,530,fill=ButtonBG,width=0)
        # reverse background color if hovered on or chosenList
        for i in xrange(8):
            if self.hoverList[i] == True:
                canvas.create_rectangle(42+(i%4)*94, 470+(i/4)*30,
                    42+94+(i%4)*94, 470+30+(i/4)*30,
                    fill="white", width=0)
            if self.chosenList[i] == True:
                canvas.create_rectangle(42+(i%4)*94, 470+(i/4)*30,
                    42+94+(i%4)*94, 470+30+(i/4)*30,
                    fill="#002E63", width=0)
        # create lines to seperate buttons
        canvas.create_line(42+94,470,42+94,530,fill="white",width=2)
        canvas.create_line(42+94*2,470,42+94*2,530,fill="white",width=2)
        canvas.create_line(42+94*3,470,42+94*3,530,fill="white",width=2)
        canvas.create_line(42,500,418,500,fill="white",width=2)
        # put button names on panel
        for i in xrange(8):
            buttonColor1 = "white" if self.hoverList[i] == False else ButtonBG
            if self.chosenList[i] == True:
                buttonColor1 = "white"
            canvas.create_text(42+47 + (i%4)*94, 470+15 + (i/4)*30,
                fill=buttonColor1,
                text=self.monitorList[i],font="airborne 15")

        #################
        # MISSION PANEL #
        #################
        canvas.create_text(30,560, anchor=NW, text="MISSION PANEL",
            font="airborne 18", fill="white")
        # draw background color for buttons
        canvas.create_rectangle(42,590,418,650,fill=ButtonBG,width=0)
        canvas.create_rectangle(42+94*3,590,42+94*4,620,fill=Slider1,width=0)
        canvas.create_rectangle(42+94*3,620,42+94*4,650,fill="red",width=0)
        # reverse background color if hovered on or chosen
        for block in xrange(8,16):
            if self.hoverList[block] == True:
                canvas.create_rectangle(42+(block%4)*94, 590+((block-8)/4)*30,
                    42+94+(block%4)*94, 590+30+((block-8)/4)*30,
                    fill="white", width=0)
            if self.chosenList[block] == True:
                canvas.create_rectangle(42+(block%4)*94, 590+((block-8)/4)*30,
                    42+94+(block%4)*94, 590+30+((block-8)/4)*30,
                    fill="#002E63", width=0)
        # create lines to seperate buttons
        canvas.create_line(42+94,590,42+94,650,fill="white",width=2)
        canvas.create_line(42+94*2,590,42+94*2,650,fill="white",width=2)
        canvas.create_line(42+94*3,590,42+94*3,650,fill="white",width=2)
        canvas.create_line(42,620,418,620,fill="white",width=2)
        # put button names on panel
        for i in xrange(8):
            buttonColor2="white" if self.hoverList[i+8] == False else ButtonBG
            if self.chosenList[i+8] == True:
                buttonColor2 = "white"
            canvas.create_text(42+47 + (i%4)*94, 590+15 + (i/4)*30,
                fill=buttonColor2,
                text=self.missionList[i], font="airborne 15")
        # special color for "run" and "abort" buttons #
        if self.hoverList[11]:
            canvas.create_text(42+47 + 3*94, 590+15, fill=Slider1,
                text=self.missionList[3], font="airborne 15")
        if self.hoverList[15]:
            canvas.create_text(42+47 + 3*94, 590+15 + 30, fill="red",
                text=self.missionList[7], font="airborne 15")
        # to make running button flashing when chosen #
        if self.chosenList[11]:
            if int(time.time() // 0.1) % 12 < 7:
                canvas.create_rectangle(42+3*94,590,42+4*94,620,
                    fill=Slider1, width=0)
                canvas.create_text(42+47 + 3*94, 590+15, fill="white",
                    text=self.missionList[3], font="airborne 15")
            else:
                canvas.create_rectangle(42+3*94,590,42+4*94,620,
                    fill="white", width=0)
                canvas.create_text(42+47 + 3*94, 590+15, fill=Slider1,
                    text=self.missionList[3], font="airborne 15")


    def drawSliders(self, canvas):
        slider_H = 22
        slider_W = 10
        # to make drawing more convinient #
        dH = slider_H/2
        dW = slider_W/2

        # VISUAL CONTROL PANEL #
        canvas.create_rectangle(435,70,885,300,fill=FrameBG, width=0)
        canvas.create_text(660, 75, anchor=N, text="VISUAL CONTROL PANEL",
            font="airborne 18", fill="white")
        for i in range(3):
            canvas.create_rectangle(445,105+i*40,540,135+i*40,
                fill=Slider1,width=0)
            canvas.create_text(492,120+i*40,text=self.visualList[i],
                font="airborne 15", fill="white")

        # slider1 #
            # centerline #
            canvas.create_line(560,120+i*40,860,120+i*40,width=4,fill="white")

            # highlight line #
            x = 560 + self.valueList[i]*3
            xEnd = x-dW
            canvas.create_line(560,120+i*40,xEnd,120+i*40,width=4,fill=Slider1)

            # slide bar
            y = 120 + i*40
            canvas.create_rectangle(x-dW,y-dH,x+dW,y+dH,fill="white",width=0)

        # empty slider #
        for i in range(3,5):
            canvas.create_rectangle(445,105+i*40,540,135+i*40,
                fill=Slider1,width=0)
            canvas.create_text(492,120+i*40,text=self.visualList[i],
                font="airborne 15", fill="white")
            y = 120 + i*40
            canvas.create_line(560,120+i*40,860,120+i*40,width=4,fill="white")
            canvas.create_line(560,120+i*40,710,120+i*40,width=4,fill=EmptyGray)
            canvas.create_rectangle(710-dW,y-dH,710+dW,y+dH,
                fill="white",width=0)


        # TRACKING POINT SAMPLING PARAMETERS #
        canvas.create_rectangle(435,330,885,680,fill=FrameBG, width=0)
        canvas.create_text(660, 335, anchor=N,
            text="TRACKING POINT SAMPLING PARAMETERS",
            font="airborne 18", fill="white")
        for j in range(8):
            canvas.create_rectangle(445,365+j*40,540,395+j*40,
                fill=Slider2,width=0)
            canvas.create_text(492,380+j*40,text=self.parameterList[j],
                font="airborne 15", fill="white")

        # slider2 #

            # centerline #
            canvas.create_line(560,380+j*40,860,380+j*40,width=4,fill="white")

            # highlight line #
            x = 560 + self.valueList[j+3]*3
            xEnd = x-dW
            canvas.create_line(560,380+j*40,xEnd,380+j*40,width=4,fill=Slider2)

            # slide bar
            y = 380 + j*40
            canvas.create_rectangle(x-dW,y-dH,x+dW,y+dH,fill="white",width=0)





        # FUNCTIONALITY CONTROL PANEL #
        canvas.create_rectangle(910,70,1360,300,fill=FrameBG, width=0)
        canvas.create_text(1135,75,anchor=N,text="FUNCTIONALITY CONTROL PANEL",
            font="airborne 18", fill="white")
        for k in range(3):
            canvas.create_rectangle(920,105+k*40,1015,135+k*40,
                fill=Slider3,width=0)
            canvas.create_text(967,120+k*40,text=self.funcList[k],
                font="airborne 15", fill="white")

        # slider3 #
            # centerline #
            canvas.create_line(1040,120+k*40,1340,120+k*40,width=4,fill="white")

            # highlight line #
            x = 1040 + self.valueList[k+11]*3
            xEnd = x-dW
            canvas.create_line(1040,120+k*40,xEnd,120+k*40,width=4,fill=Slider3)

            # slide bar
            y = 120 + k*40
            canvas.create_rectangle(x-dW,y-dH,x+dW,y+dH,fill="white",width=0)

        # battery percentage #
        for k in range(3,4):
            canvas.create_rectangle(920,105+k*40,1015,135+k*40,
                fill=Slider3,width=0)
            canvas.create_text(967,120+k*40,text=self.funcList[k],
                font="airborne 15", fill="white")

            # centerline #
            canvas.create_line(1040,120+k*40,1340,120+k*40,width=4,fill="white")

            # highlight line #
            status = self.conn.root.getStatus() #-> status dict
            for key in status:
                if key == "BATT":
                    xEnd = int(status[key])*3 + 1040
            canvas.create_line(1040,120+k*40,xEnd,120+k*40,width=4,fill=Slider3)

        # empty slider #
        for k in range(4,5):
            canvas.create_rectangle(920,105+k*40,1015,135+k*40,
                fill=Slider3,width=0)
            canvas.create_text(967,120+k*40,text=self.funcList[k],
                font="airborne 15", fill="white")
            y = 120 + k*40
            canvas.create_line(1040,120+k*40,1340,120+k*40,width=4,fill="white")
            canvas.create_line(1040,120+k*40,1190,120+k*40,width=4,
                fill=EmptyGray)
            canvas.create_rectangle(1190-dW,y-dH,1190+dW,y+dH,
                fill="white",width=0)



# MISSION STATUS OVERVIEW #
    def drawInfoBar(self, canvas):

        # draw background #
        canvas.create_rectangle(910,330,1360,680,fill=FrameBG, width=0)
        canvas.create_text(1135, 343, anchor=N, text="MISSION STATUS OVERVIEW",
            font="airborne 18", fill="white")
        for i in range(5):
            y0 = 380 + 60*i
            y1 = y0 + 30
            canvas.create_rectangle(910,y0,1360,y1,fill=ButtonBG, width=0)
        canvas.create_line(1060,380,1060,680,fill="white",width=3)



    # draw status #
        status = self.conn.root.getStatus() #-> status dict

        statusDic = interpretKeyValue(status)
        if not self.unitAdded:
            statusDic = addUnit(statusDic)
            self.unitAdded = True


        keyNames = {'STAT': "STATUS", 'ACTT': "ACTIVE TIME",
                    'MIST': "MISSION TIME", 'DELY': "DELAY",
                    'GATC': "GATES COUNT", 'SPED': "SPEED",
                    'PROT': "PROC DELAY", 'CVST': "CV STATUS",
                    'BATT': "BATT VOLT", 'ADDR': "IP ADDRESS"
                   }
        keyOrder = {'STAT': 0, 'ACTT': 1,
                    'MIST': 2, 'DELY': 3,
                    'GATC': 4, 'SPED': 5,
                    'PROT': 6, 'CVST': 7,
                    'BATT': 8, 'ADDR': 9
                   }


        # draw item #
        for key in statusDic:
            keyName = keyNames[key]
            i = keyOrder[key]
            canvas.create_text(985,395+i*30,text=keyName,font="airborne 15",
                fill="white")
            canvas.create_text(1210,395+i*30,text=statusDic[key],
                font="airborne 15",fill="white")




        # status = {
        #     'STAT': STAT_ONLINE, 'ACTT': 0, 'MIST': 0, 'DELY': 0,
        #     'GATC': 0, 'SPED': 0, 'PROT': 0, 'CVST': STAT_ONLINE,
        #     'BATT': 100, 'ADDR': socket.gethostname()
        # }
        # @key:
        # STAT: (int) status of mobot
        # ACTT: (int) active time in seconds
        # MIST: (int) mission time in seconds
        # DELY: (int) internet delay in milliseconds
        # GATC: (int) count of gates passed
        # SPED: (int) current mobot speed
        # PROT: (int) process time for cv
        # CVST: (int) status of cv
        # BATT: (int) battery percentage
        # ADDR: (str) address of service machine (can be mobot)





    def redrawAll(self):
        canvas = self.canvas
        self.drawBasic(canvas)























the_flash = Interface()
the_flash.run()
