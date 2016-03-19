#####################################
# Debug Panel Interface Logic Layer #
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

import sys
import time
import rpyc
import socket
import threading
import Tkinter as tk
from utils import speak, speaklog, info
from rpyc.utils.server import ThreadedServer

# This interface is half-hardcoded, for the sake of simplicity
# There are two kinds of main input sources: buttons and slides

# This is the interface layer between GUI and logic

# Connection Configuration
# This is the address and port number of raspberry pi control server
MOBOT_ADDR = "128.237.216.97"
MOBOT_PORT = 15112
BACKBONE_PORT = 15251
VIDEO_PORT = 20000
# Port Convention:
# MOBOT_PORT = 15112
# BACKBONE_PORT = 15251

# Global Constants:
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

speaklog("system initializing", block=True)

class InterfaceService(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        speaklog("service instance created")

        self.filterstate = FILTER_ORIG
        self.taskstate = TASK_IDLE
        self.taskrunning = False

        self.values = {
            'BRIG': 0, 'CNST': 50, 'BLUR': 4,
            'THRS': 150, 'SIZE': 4, 'CERT': 0.7, 'PTS': 5, 'RADI': 10,
                'A': 0.6, 'B': 0.3, 'C': 0.1,
            'TCHS': 0.5, 'GATG': 14, 'MAXS': 100
        }
        # @key:
        # BRIG: (int) [0,100] brightness
        # CNST: (int) [0,100] contrast
        # BLUR: (int) [0,20] blur index
        # -----------------------------
        # THRS: (int) [0,255] threshold for sample point in grayscale
        # SIZE: (int) [0,10] sample matrix size
        # CERT: (float) [0,1) quality of desired sample point
        #
        # PTS : (int) [0,5] number of sample points
        # RADI: (int) [1,15] radius of sample disk
        # A   : (float) [0,1] possibility of alpha region
        # B   : (float) [0,1] possibility of beta region
        # C   : (float) [0,1] possibility of gamma region
        # -----------------------------
        # TCHS: (float) [0.1,0.9] touch sensitivity
        # GATG: (int) [1,20] gate target count
        # MAXS: (int) [0,255] maximum speed

        self.status = {
            'STAT': STAT_DISCONNECTED, 'ACTT': 0, 'MIST': 0, 'DELY': 0,
            'GATC': 0, 'SPED': 0, 'PROT': 0, 'CVST': STAT_DISCONNECTED,
            'BATT': 100, 'ADDR': socket.gethostname()
        } # This is a placeholder in case mobot is offline
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

        self.trackingpts = []
        # Connection instance
        self.conn = None
        self.updatestop = threading.Event()
        self.updatethd = threading.Thread(target=self.updateInfo,
            args=(self.updatestop,))

    def on_connect(self):
        speaklog("connection established")
        self.exposed_connectToMobot()
        self.updatethd.start()

    def on_disconnect(self):
        speaklog("connection lost")
        self.conn = None
        self.updatestop.set()
        self.exposed_disconnectFromMobot()
        self.updatestop.clear()

    def updateInfo(self, stop_event):
        while not stop_event.is_set():
            try:
                if self.conn == None: return
                statnow = self.conn.root.getMobotStatus()
                # valnow = self.conn.root.getMobotValues()
                pts = self.conn.root.getTrackingPts()
                for key in self.status:
                    self.status[key] = statnow[key]

                # for key in self.values:
                    # valnow[key] = self.values[key]

                del self.trackingpts[:]
                for pt in pts:
                    self.trackingpts.append(pt)
            except:
                warn("info update failed")
            time.sleep(0.1)

    def exposed_connectToMobot(self, addr=MOBOT_ADDR, port=MOBOT_PORT):
        try:
            self.conn = rpyc.connect(addr, port)
            if self.conn.root.recognized():
                speaklog("connected to mobot, syncing data")
                return 0
            else:
                speaklog("connection refused")
                return 2
        except:
            speaklog("service unavailable")
            return 1

    def exposed_disconnectFromMobot(self):
        # Reset Status to placeholder
        if self.conn != None: self.conn.close()
        self.status = {
            'STAT': STAT_DISCONNECTED, 'ACTT': 0, 'MIST': 0, 'DELY': 0,
            'GATC': 0, 'SPED': 0, 'PROT': 0, 'CVST': STAT_DISCONNECTED,
            'BATT': 100, 'ADDR': socket.gethostname()
        }
        self.values = {
            'BRIG': 0, 'CNST': 50, 'BLUR': 4,
            'THRS': 150, 'SIZE': 4, 'CERT': 0.7, 'PTS': 5, 'RADI': 10,
                'A': 0.6, 'B': 0.3, 'C': 0.1,
            'TCHS': 0.5, 'GATG': 14, 'MAXS': 100
        }
        del self.trackingpts[:]

    def exposed_startStream(self, addr, port):
        return # TODO: this method is slow and consumes bandwidth
        if self.conn == None:
            if self.exposed_connectToMobot(addr, port) != 0:
                return
        self.conn.root.startVideoStream(VIDEO_PORT)

    def exposed_getStatus(self):
        # if self.conn != None and not self._updated:
        #     self.status = self.conn.root.getMobotStatus()
        #     self._updated = True
        return self.status

    def exposed_getTrackingPts(self):
        # if self.conn != None and not self._updated:
        #     self.trackingpts = self.conn.root.getTrackingPts()
        #     self._updated = True
        return self.trackingpts

    def exposed_resetStatus(self):
        speaklog('status reset')
        self.status['STAT'] = STAT_ONLINE
        # TODO: do something to reset status

    def exposed_abortMission(self):
        if self.taskrunning:
            self.taskrunning = False
            speaklog('mission aborted')
            self.status['STAT'] = STAT_ABORT
            # TODO: do something to abort mission

    def exposed_startMission(self):
        if not self.taskrunning:
            self.taskrunning = True
            speaklog('mission is a go')
            self.status['STAT'] = STAT_MISSION
            # TODO: do something to trigger mission

            # Temp Unit Test For Video:
            self.exposed_startStream(MOBOT_ADDR, MOBOT_PORT)
            # Temp Unit Test For Framework CV:
            # self.exposed_connectToMobot()

    def exposed_updateValues(self, filterstates, taskstates, slides):
        # @param:
        # filterstates: (dict) the state list of fliter
        # taskstates: (dict) the state list of task
        # slides: (dict) the values of slidebars

        #assert(set(filterstates.keys()) == set(FILTER_KEYS))
        #assert(set(taskstates.keys()) == set(TASK_KEYS))
        #assert(set(slides.keys()) == set(SLIDE_KEYS))

        # Tell filter status
        for key in filterstates:
            if filterstates[key]:
                # Set filter state to chosen
                self.filterstate = FILTER_KEYS.index(key)

        # Tell task status
        for key in taskstates:
            if taskstates[key]:
                # Set task state to chosen
                self.taskstate = TASK_KEYS.index(key)

        # Update Key Values
        for key in slides:
            self.values[key] = slides[key]

        speaklog("%s, %s"%(FILTER_NAMES[self.filterstate],
            TASK_NAMES[self.taskstate]))

if __name__ == "__main__":
    print flash
    info("initiating server")
    server = ThreadedServer(InterfaceService, port = BACKBONE_PORT)
    speaklog("ready to accept connections")
    server.start()
