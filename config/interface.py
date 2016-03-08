import Tkinter as tk

event_dict = {
    2: "KeyPress",
    3: "KeyRelease",
    4: "ButtonPress",
    5: "ButtonRelease",
    6: "Motion",
    7: "Enter",
    8: "Leave",
    9: "FocusIn",
    10: "FocusOut",
    12: "Expose",
    15: "Visibility",
    17: "Destroy",
    18: "Unmap",
    19: "Map",
    21: "Reparent",
    22: "Configure",
    24: "Gravity",
    26: "Circulate",
    28: "Property",
    32: "Colormap",
    36: "Activate",
    37: "Deactivate",
    38: "MouseWheel"
}


class Widget(object):
    # Override these methods when creating your own animation
    def __init__(self, x, y, w, h, parent=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.parent = parent
        self.children = []
        # The register dict registers event listeners for implementation of
        # binding of events. This mimics the behaviour in tk where events
        # need to be binded (SIMPLE ALGO)
        self.register = {
            "<ButtonPress>": [],
            "<Motion>": [],
            "<ButtonRelease>": [],
            "<KeyRelease>": []
        }

    def add(self, widget, relx, rely):
        # This ignores where the widget is inited, at any x, y.
        # Gives widget new absolute location for the sake of simplicity
        # NOTE: Might be wrong for complicated models, and not viable for
        # dynamically changing location of widgets
        # NOTE: A widget will not be drawen until it is added to a parent
        # that has indirect or direct link to the application level
        self.children.append(widget)
        widget.parent = self
        widget.x = relx + self.x
        widget.y = rely + self.y

    def collides(self, x, y):
        # Evaluates whether the event is colliding with the widget or not
        # @param:
        # x: (int) the x position of event
        # y: (int) the y position of event
        # TODO: TO BE IMPLEMENTED!
        return False

    def bind(self, event_type, method):
        # Mimics the bind in tk
        if event_type in self.register.keys():
            self.register[event_type].append(method)

    def propagate(self, event):
        # If event is not handled: pass to children, or on its will
        for w in self.children:
            if w.collides(event.x, event.y):
                # NOTE: This might be buggy: x, y rel to upper left of canvas
                # while widgets containing another might prefer to receive rel
                # x and y to their parents because they do not know their abs
                # location on screen
                # NOTE: This does not necessarially mean that the widget wants
                # the event. For advanced implementations we need to support
                # binding of events # NOTE: I implemented it.
                if event_dict[event.type] in self.register.keys():
                    w.event(event)

    def event(self, event):
        handled = False
        # Process event for specific widget
        # NOTE: To be overridden
        # example: if event.type == 4: self.foo()
        # Propagate event if widget wishes to
        if not handled:
            self.propagate(event)

    def draw(self, canvas):
        # To be implemented by subclasses
        # Draws the content in widget onto canvas
        pass

# TODO: I havent changed this part yet. It so far does not support our
# framework.
class Application(object):
    def __init__(): pass
    def keyPressed(self, event): pass
    def timerFired(self): pass
    def redrawAll(self): pass
    
    # Call app.run(width,height) to get your app started
    def run(self, width=300, height=500):
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

        def keyReleasedWrapper(event):
            self.keyPressed(event)
            redrawAllWrapper()

        root.bind("<Button-1>", mousePressedWrapper)
        root.bind("<Motion>", mouseMotionWrapper)
        root.bind("<ButtonRelease>", mouseReleasedWrapper)
        # root.bind("<Double-Button-1>", doubleClickedWrapper)
        root.bind("<KeyRelease>", keyReleasedWrapper)

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
