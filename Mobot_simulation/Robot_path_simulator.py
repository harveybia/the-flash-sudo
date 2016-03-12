from Animation import Animation
from Robot import *
from matt_GUI import *

class Stuct(object): pass

BOARD = Stuct()
BOARD.left = 0
BOARD.top = 0
BOARD.right = 800
BOARD.bottom = 600

# def sqrWave(x):
#     amp = 30
#     length = 0.2
#     result = []

#     if abs(x % length) <= 0.002:
#         for i in range(-amp, amp + 1):
#             result.append(i)
#     elif (x // length) % 2 == 0:
#         result.append(amp)
#     else:
#         result.append(-amp)

#     return result

def sinWave(t):
    return Vec2D(20 * math.sin(10 * t), t * BOARD.bottom)

class Simulator(Animation):
    def __init__(self, margin = 10):
        self.path = Path(sinWave,
            BOARD.right, BOARD.bottom)
        self.PID = Robot_PID(5, BOARD.right, BOARD.bottom, self.path, 0.5,0,0.1)
        self.initGUI(margin)
        self.run(BOARD.right, BOARD.bottom)

    def initGUI(self, margin):
        btn_w = 40
        btn_h = 20
        scrl_w = 10
        scrl_h = 80
        ctrlPanel = GUI_Rect(margin, margin, 
            BOARD.right / 3 - margin, BOARD.bottom - margin)
        resetBtn = Button(margin, margin,
                          margin + btn_w, margin + btn_h, 
            text = "Reset", parent = ctrlPanel, func = self.reset)
        speed = Scroller(margin, btn_h + 2 * margin,
                        margin + scrl_w, btn_h + 2 * margin + scrl_h,
                        amount = 20, parent = ctrlPanel)
        self.ctrlPanel = ctrlPanel
        self.speed = speed
        self.resetBtn = resetBtn

    def reset(self):
        self.path = Path(sinWave,
            BOARD.right, BOARD.bottom)
        self.PID = Robot_PID(5, BOARD.right, BOARD.bottom, self.path, 0.5,0,0.1)

    def mousePressed(self, event):
        self.ctrlPanel.onMouseDown(event.x, event.y)
    def keyPressed(self, event): pass
    def keyReleased(self,event):pass
    def leftMouseReleased(self,event):
        self.ctrlPanel.onMouseUp(event.x, event.y)
    def mouseMotion(self,event):
        self.ctrlPanel.onMouseMove(event.x, event.y)
        self.speed.onMouseMove(event.x,event.y)
    def timerFired(self): 
        self.PID.update()
    def init(self): pass
    def redrawAll(self): 
        self.PID.draw(self.canvas)
        self.path.draw(self.canvas)
        self.ctrlPanel.draw(self.canvas)

main = Simulator()