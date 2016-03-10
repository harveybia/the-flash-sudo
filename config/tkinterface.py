#####################################
# Debug Panel Interface Logic Layer #
# copyright 2015-2016 Harvey Shi    #
#####################################

import Tkinter as tk
import sys
import time
import rpyc
from utils import speak, speaklog, info
from rpyc.utils.server import ThreadedServer

# This interface is half-hardcoded, for the sake of simplicity
# There are two kinds of main input sources: buttons and slides

# This is the interface layer between GUI and logic

# Global Constants:
FILTER_ORIG   = 0 # Original Video
FILTER_PROC   = 1 # Processed Image (Canny Edges)
FILTER_BW     = 2 # Black & White View
FILTER_IRNV   = 3 # Inverted Image
FILTER_CV     = 4 # Computer Vision Mode, With TRAC PT, BEZIER CURVE
FILTER_PRED   = 5 # Predictive Mode
FILTER_HYBRID = 6 # Hybrid Mode: ORIG + TRAC PT + PRED + CV

FILTER_KEYS   = ['ORIG', 'PROC', 'BW', 'IRNV', 'CV', 'PRED', 'HYBR', 'BLUR']

TASK_IDLE     = 0 # IDLE State
TASK_DEBUG    = 1 # Debug Mode
TASK_TRACE    = 2 # Line Trace
TASK_CAMERA   = 3 # Capture Camera Feed
TASK_TEST     = 4 # Test Trial

TASK_KEYS   = ['IDLE', 'DEBU', 'TRAC', 'CAM', 'TEST']

# Constants for Value slide controls:
SLIDE_KEYS = [
    'BRIG', 'CNST', 'BLUR',
    'THRS', 'SIZE', 'CERT', 'PTS', 'RADI', 'A', 'B', 'C',
    'TCHS', 'GATG', 'MAXS'
    ]

speaklog("system initializing", block=True)

class Interface(rpyc.Service):
    def __init__(self, *args, **kwargs):
        rpyc.Service.__init__(self, *args, **kwargs)
        speaklog("service instance created")

        self.filterstate = FILTER_ORIG
        self.taskstate = TASK_IDLE
        self.taskrunning = False

        self.values = {
            'BRIG': 0, 'CNST': 50, 'BLUR': 4,
            'THRS': 150, 'SIZE': 4, 'CERT': 0.7, 'PTS': 5, 'RADI': 6,
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
        # TCHS: (int) [0.1,0.9] touch sensitivity
        # GATG: (int) [1,20] gate target count
        # MAXS: (int) [0,255] maximum speed

    def on_connect(self):
        speaklog("connection established")

    def on_disconnect(self):
        speaklog("connection lost")

    def exposed_abortMission(self):
        if self.taskrunning:
            self.taskrunning = False
            speaklog('mission aborted')
            # TODO: do something to abort mission

    def exposed_startMission(self):
        if not self.taskrunning:
            self.taskrunning = True
            speaklog('mission is a go')
            # TODO: do something to trigger mission

    def exposed_updateValues(self, filterstates, taskstates, slides):
        # @param:
        # filterstates: (dict) the state list of fliter
        # taskstates: (dict) the state list of task
        # slides: (dict) the values of slidebars
        assert(set(filterstates.keys()) == set(FILTER_KEYS))
        assert(set(taskstates.keys()) == set(TASK_KEYS))
        assert(set(slides.keys()) == set(SLIDE_KEYS))

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

        speaklog("values updated")

if __name__ == "__main__":
    info("initiating server")
    server = ThreadedServer(Interface, port = 15251)
    speaklog("ready to accept connections")
    server.start()
