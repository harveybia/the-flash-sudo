from tkinter import *

class Animation(object):

    DELAY = 20
    # Override these methods when creating your own animation
    def mousePressed(self, event): pass
    def keyPressed(self, event): pass
    def keyReleased(self,event):pass
    def leftMouseReleased(self,event):pass
    def mouseMotion(self,event):pass
    def timerFired(self): pass
    def init(self): pass
    def redrawAll(self): pass
    
    # Call app.run(width,height) to get your app started
    def run(self, width=800, height=600):
        # create the root and the canvas
        root = Tk()
        root.title("Evolution")
        m1 = PanedWindow()
        m1.pack(fill=BOTH, expand = 1)
        self.width = width
        self.height = height
        self.canvas = Canvas(root, width = width, height = height)
        self.canvas.pack()
        self.toolbar = Canvas(root, width=width/2, height=height)
        self.toolbar
        m1.add(self.canvas)
        self.window = m1

        # set up events
        def redrawAllWrapper():
            self.canvas.delete(ALL)
            self.redrawAll()
            self.canvas.update()

        def mousePressedWrapper(event):
            self.mousePressed(event)
            redrawAllWrapper()

        def keyPressedWrapper(event):
            self.keyPressed(event)
            redrawAllWrapper()

        root.bind("<Button-1>", mousePressedWrapper)
        root.bind("<Key>", keyPressedWrapper)
        root.bind("<KeyRelease>", self.keyReleased)
        root.bind("<Motion>", self.mouseMotion)
        root.bind("<B1-ButtonRelease>", self.leftMouseReleased)

        # set up timerFired events
        self.timerFiredDelay = Animation.DELAY # milliseconds
        def timerFiredWrapper():
            self.timerFired()
            redrawAllWrapper()
            # pause, then call timerFired again
            self.canvas.after(self.timerFiredDelay, timerFiredWrapper)
            
        # init and get timerFired running
        self.init()
        timerFiredWrapper()
        # and launch the app
        root.mainloop()
        print("Bye")



