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
from Tkinter import *
import subprocess

ADDR, PORT = 'localhost', 15251
# Video Configuration
V_WIDTH, V_HEIGHT = 320, 240

newaddr = raw_input("Backbone server adderss, leave empty for localhost: ")
if newaddr != "": ADDR = newaddr
newport = raw_input("Port number, leave empty for 15251: ")
if newport != "": ADDR = newaddr
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
    im = Image.fromarray(grayToRGB(img))
    return ImageTk.PhotoImage(im)

def startVideoStream(addr="", port=15122):
    return cv2.VideoCapture(0)

def readTkImage(stream):
    ret, frame = stream.read()
    if ret:
        return _rgbToTkImage(frame)
    else:
        return Image(width=V_WIDTH, height=V_HEIGHT)

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
        self.__init__()
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
        self.valueList = [0] * 14
        self.startRun = False

        # Connection to backbone server
        self.conn = rpyc.connect(ADDR, PORT)

        # Connection to raw video stream
        self.video = startVideoStream()
        #readTkImage(self.video)

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
        elif x0<=x<=x1 and y0<=y<=y1:
            for i in xrange(8):
                if self.hoverList[i] == True:
                    self.chosenList[i] = True
                else: self.chosenList[i] = False
        elif x0<=x<=x1 and y2<=y<=y3:
            for j in xrange(8, 16):
                if self.hoverList[j] == True:
                    self.chosenList[j] = True
                    # pressing other buttons also terminates running
                    self.chosenList[11] = False
                    self.startRun = False
                else: self.chosenList[j] = False

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

    def sendData(self):
        filterDic, taskDic, slideDic = self.getData()
        # data transfer protocol
        self.conn.root.updateValues(filterDic, taskDic, slideDic)

    def getData(self):
        FILTER_KEYS   = ['ORIG', 'PROC', 'BW', 'IRNV', 'CV', 'PRED', 'HYBR', 'BLUR']
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

    def drawCaption(self, canvas):
        canvas.create_text(15, 15, anchor=NW, text="THE-FLASH-SUDO",
            font="airborne 24 bold", fill="white")
        canvas.create_text(222,15, anchor=NW, text="MISSION MONITOR",
            font="airborne 24", fill="gray75")
        date = subprocess.check_output(["date"]).decode("utf-8")
        canvas.create_text(23, 45, anchor=NW, text=date,
            font="Airborne-II-Pilot 16", fill="gray85")

    def drawVideo(self, canvas):
        canvas.create_text(30, 90, anchor=NW, text="LIVE FEED",
            font="airborne 18", fill="white")
        canvas.create_text(230,120,anchor=N,text="FRONT",
            font="airborne 16",fill="white")
        canvas.create_rectangle(42,119,418,401,fill="#1C75BC",width=0)
        # real video canvas
        canvas.create_rectangle(70,140,390,380,fill="#1C75BC",width=2)
        # draw diagonals
        canvas.create_line(42,119,418,401,width=2)
        canvas.create_line(418,119,42,401,width=2)

    def drawButtons(self, canvas):
        ####################
        # MONITOR SELECTOR #
        ####################
        canvas.create_text(30,440, anchor=NW, text="MONITOR SELECTOR",
            font="airborne 18", fill="white")
        # draw background color for buttons
        canvas.create_rectangle(42,470,418,530,fill="#1C75BC",width=0)
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
            buttonColor1 = "white" if self.hoverList[i] == False else "#1C75BC"
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
        canvas.create_rectangle(42,590,418,650,fill="#1C75BC",width=0)
        canvas.create_rectangle(42+94*3,590,42+94*4,620,fill="#39B54A",width=0)
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
            buttonColor2="white" if self.hoverList[i+8] == False else "#1C75BC"
            if self.chosenList[i+8] == True:
                buttonColor2 = "white"
            canvas.create_text(42+47 + (i%4)*94, 590+15 + (i/4)*30,
                fill=buttonColor2,
                text=self.missionList[i], font="airborne 15")
        # special color for "run" and "abort" buttons #
        if self.hoverList[11]:
            canvas.create_text(42+47 + 3*94, 590+15, fill="#39B54A",
                text=self.missionList[3], font="airborne 15")
        if self.hoverList[15]:
            canvas.create_text(42+47 + 3*94, 590+15 + 30, fill="red",
                text=self.missionList[7], font="airborne 15")
        # to make running button flashing when chosen #
        if self.chosenList[11]:
            if int(time.time() // 0.1) % 12 < 7:
                canvas.create_rectangle(42+3*94,590,42+4*94,620,
                    fill="#39B54A", width=0)
                canvas.create_text(42+47 + 3*94, 590+15, fill="white",
                    text=self.missionList[3], font="airborne 15")
            else:
                canvas.create_rectangle(42+3*94,590,42+4*94,620,
                    fill="white", width=0)
                canvas.create_text(42+47 + 3*94, 590+15, fill="#39B54A",
                    text=self.missionList[3], font="airborne 15")


    def drawSliders(self, canvas):
        pass

    def redrawAll(self):
        canvas = self.canvas
        self.drawBasic(canvas)


























the_flash = Interface()
the_flash.run()
