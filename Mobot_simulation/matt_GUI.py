# Made by "Matt" Yixiu Zhao

# New version adapted for Mobot Simulation

from Animation import Animation

from tkinter import *

import string

# From course notes
def rgbString(red, green, blue):
    return "#%02x%02x%02x" % (red, green, blue)

LIGHTBLUE = rgbString(191,239,255)

# I wrote the rest of these
class Rect(object):
    def __init__(self, x1, y1, x2, y2, color = "white", border = 0,
     activeFill = None):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.color = color
        self.border = border
        if activeFill == None: self.activeFill = color
        else: self.activeFill = activeFill

    def getPos(self):
        return (self.x1,self.y1)

    def inBorders(self,x,y):
        x1, y1 = self.getPos()
        return (x >= x1 and x <= x1 + self.width 
            and y >= y1 and y <= y1 + self.height)

    def constrainInBorders(self,x,y):
        x1, y1 = self.getPos()
        if x < x1: x = x1
        elif x > x1 + self.width: x = x1 + self.width
        if y < y1: y = y1
        elif y > y1 + self.height: y = y1 + self.height
        return (x,y)

    def getCenter(self):
        return (self.getPos()[0] + self.width / 2, 
                self.getPos()[1] + self.height / 2)

    def draw(self,canvas,mask = None):
        x1, y1 = self.getPos()
        x2, y2 = x1 + self.width, y1 + self.height
        if mask != None:
            x1, y1 = mask.constrainInBorders(x1, y1)
            x2, y2 = mask.constrainInBorders(x2, y2)
        canvas.create_rectangle(x1, y1, x2, y2,
            fill = self.color, width = self.border,activefill = self.activeFill)

WORLD = Rect(0,0,0,0)

class GUI_Rect(Rect):
    def __init__(self, x1, y1, x2, y2, 
            color = "white", border = 0, parent = WORLD,activeFill = None):
        super().__init__(x1,y1,x2,y2,color,border,activeFill)
        self.parent = parent
        if parent != WORLD: parent.addGUIItem(self)
        self.isVisible = True
        self.GUIItems = []

    def getPos(self):
        parentPos = self.parent.getPos()
        return (parentPos[0] + self.x1, parentPos[1] + self.y1)

    def addGUIItem(self, item):
        if isinstance(item,GUI_Rect):
            self.GUIItems.append(item)
            item.parent = self
        else: print(False)

    def draw(self, canvas, mask = None, activeFill = "white"):
        super().draw(canvas, mask)
        for item in self.GUIItems:
            item.draw(canvas, mask)

    def onMouseDown(self,x,y):
        for item in self.GUIItems:
            item.onMouseDown(x,y)

    def onMouseUp(self,x,y):
        for item in self.GUIItems:
            item.onMouseUp(x,y)

    def onMouseMove(self,x,y):
        for item in self.GUIItems:
            item.onMouseMove(x,y)

class Button(GUI_Rect):

    CHOSEN_BORDER = 4
    NORMAL_BORDER = 1

    def __init__(self, x1, y1, x2, y2, color = "white", enabled = True,
                 border = 1, 
                 parent = WORLD, text = "Button", func = lambda:print(42), 
                 anchor = "s",activeFill = "white"):
        super().__init__(x1,y1,x2,y2,color,border,parent,activeFill)
        self.parent = parent
        self.activeFill = activeFill
        self.chosen = False
        self.normalBorder = border
        self.text = text
        self.func = func
        self.anchor = anchor

    def setChosen(self,value):
        self.chosen = value
        if self.chosen: self.border = Button.CHOSEN_BORDER
        else: self.border = self.normalBorder

    def onClick(self):
        self.func()

    def onMouseDown(self,x,y):
        if self.inBorders(x,y):
            self.onClick()

    def draw(self,canvas,mask = None):
        super().draw(canvas,mask)
        x, y = self.getCenter()
        if mask != None and not mask.inBorders(x,y): return
        else:
            if self.anchor == "s":
                canvas.create_text(x,y,text = self.text)
            elif self.anchor == "l":
                canvas.create_text(x - self.width / 2, y, text = self.text,
                    anchor = "w")

class Selection(GUI_Rect):
    def __init__(self, x1, y1, x2, y2, spacing, buttons = None,
                parent = WORLD, color = "white", border = 0, align = "v"):
        super().__init__(x1,y1,x2,y2,color,border)
        self.parent = parent
        self.spacing = spacing
        self.buttons = []
        self.current = 0
        if buttons == None: 
            self.buttonHeight = None
            return
        else:
            self.buttonCount = len(buttons)
        if align == "v":
            self.buttonHeight = (self.height - 
                self.spacing * (self.buttonCount - 1)) / self.buttonCount
            for i in range(self.buttonCount):
                by1 = i * (self.spacing + self.buttonHeight)
                newButton = Button(0, by1, self.width, by1 + self.buttonHeight,
                 parent = self, **buttons[i])
                self.buttons.append(newButton)
        self.buttons[self.current].setChosen(True)

    def draw(self,canvas,mask = None):
        super().draw(canvas,mask)
        for button in self.buttons:
            button.draw(canvas,mask)

    def setChosenButton(self,i):
        for button in self.buttons:
            button.setChosen(False)
        self.buttons[i].setChosen(True)

    def onMouseDown(self,x,y):
        for i in range(len(self.buttons)):
            button = self.buttons[i]
            if button.inBorders(x,y):
                self.setChosenButton(i)
                button.onClick()
                return

class Scroller(GUI_Rect):

    MIN_HEIGHT = 10

    def __init__(self, x1, y1, x2, y2, amount, color = "white", parent = WORLD):
        super().__init__(x1,y1,x2,y2,color,border = 1,parent = parent)
        self.amount = amount
        self.value = 0
        self.ratio = 1
        self.btnHeight = self.height - self.amount
        self.button = Button(0,0,self.width,self.btnHeight,
            "grey",parent = self, text = "")
        self.mouseDrag = False
        self.mouseOffset = None

    # This must occur in the button region
    def onMouseDown(self,x,y):
        if self.button.inBorders(x,y):
            self.mouseDrag = True
            x1, y1 = self.button.getPos()
            self.mouseOffset = y - y1

    def getValue(self):
        return self.value

    def onMouseUp(self,x,y):
        self.mouseDrag = False

    def setAmount(self,amount):
        if amount < self.amount and self.value > amount:
            self.value = amount
        if amount > self.height - Scroller.MIN_HEIGHT:
            # One distance represents more value as button can't become smaller
            self.ratio = amount / (self.height - Scroller.MIN_HEIGHT)
        self.amount = amount
        self.button.y1 = self.value / self.ratio
        self.buttonHeight = max(self.height - self.amount,Scroller.MIN_HEIGHT)
        self.button.height = self.buttonHeight

    def onMouseMove(self,x,y):
        y0 = self.getPos()[1]
        if self.mouseDrag:
            self.button.y1 = y - y0 - self.mouseOffset
            if self.button.y1 < 0:
                self.button.y1 = 0
            elif self.button.y1 + self.button.height > self.height:
                self.button.y1 = self.height - self.button.height
            self.value = self.button.y1 * self.ratio

    def draw(self,canvas,mask = None):
        super().draw(canvas,mask)
        self.button.draw(canvas,mask)

class SelectionWindow(GUI_Rect):

    def __init__(self,x1,y1,x2,y2,margin = 10, itemHeight = 20, parent = WORLD, 
        scrolbarWidth = 15, border = 0, color = "white"):
        super().__init__(x1,y1,x2,y2,color,border)
        self.margin = margin
        self.itemCount = 0
        self.itemHeight = itemHeight
        self.colors = [rgbString(240,240,240),"white"]
        self.mask = GUI_Rect(margin,margin,
            self.width - margin,self.height - margin, parent = self)
        self.selection = Selection(margin,margin,
            self.width - margin - scrolbarWidth ,margin,0, parent = self)
        self.scroller = Scroller(self.width - margin - scrolbarWidth,
                                 margin,
                                 self.width - margin, self.height - margin, 0, 
                                 parent = self)

    def addItem(self,name,func):
        newButton = Button(0, self.itemCount * self.itemHeight,
            self.selection.width, (self.itemCount + 1) * self.itemHeight,
            color = self.colors[self.itemCount % 2], text = name, func = func,
            border = 0, parent = self.selection, anchor = "l")
        self.itemCount += 1
        self.selection.buttons.append(newButton)
        self.selection.height += self.itemHeight
        if self.selection.height > self.mask.height:
            self.scroller.setAmount(self.selection.height - self.mask.height)

    def draw(self,canvas,mask = None):
        super().draw(canvas,mask)
        self.selection.draw(canvas,self.mask)
        self.scroller.draw(canvas,mask)
        x1, y1 = self.getPos()
        canvas.create_rectangle(x1 + 1, y1 + 1, x1 + self.width - 1,
             y1 + self.margin - 1, 
            fill = self.color, width = 0)
        canvas.create_rectangle(x1 + 1, y1 + self.height - self.margin + 1
            , x1 + self.width - 1, y1 + self.height - 1, 
            fill = self.color, width = 0)

    def onMouseDown(self,x,y):
        if self.scroller.inBorders(x,y):
            self.scroller.onMouseDown(x,y)
        if self.mask.inBorders(x,y):
            self.selection.onMouseDown(x,y)

    def onMouseUp(self,x,y):
        self.scroller.onMouseUp(x,y)
        if self.mask.inBorders(x,y):
            self.selection.onMouseUp(x,y)

    def onMouseMove(self,x,y):
        self.scroller.onMouseMove(x,y)
        self.selection.y1 = self.margin - self.scroller.value

    def clear(self):
        self.itemCount = 0
        self.selection.buttons = []
        self.selection.current = 0
        self.scroller.amount = 0
        self.scroller.value = 0
        self.selection.y1 = self.margin

class DragWindow(GUI_Rect):
    def __init__(self,x1,y1,x2,y2,content,margin = 20,color = "white",
        border = 0, parent = WORLD):
        super().__init__(x1,y1,x2,y2,color,border,parent)
        self.xoffset = 0
        self.yoffset = 0
        self.mouseStartx = 0
        self.mouseStarty = 0
        self.isDragging = False
        self.content = content
        self.contentx = content.x1
        self.contenty = content.y1        
        self.cover = []
        x,y = self.getPos()
        self.cover.append(GUI_Rect(-margin,-margin,self.width + margin,0,
            color,border = 0, parent = self))
        self.cover.append(GUI_Rect(-margin,-margin,0,self.height + margin,
            color,border = 0, parent = self))
        self.cover.append(GUI_Rect(self.width,-margin,self.width + margin,
            self.height + margin, color,border = 0, parent = self))
        self.cover.append(GUI_Rect(-margin,self.height,self.width + margin,
            self.height + margin, color,border = 0, parent = self))

    def setContent(self,content):
        self.content = content

    def onMouseDown(self,x,y):
        if not self.isDragging:
            self.mouseStartx = x
            self.mouseStarty = y
            self.isDragging = True

    def onMouseMove(self,x,y):
        if self.isDragging:
            self.xoffset = x - self.mouseStartx
            self.yoffset = y - self.mouseStarty
            self.content.x1 = self.contentx + self.xoffset
            self.content.y1 = self.contenty + self.yoffset

    def onMouseUp(self,x,y):
        self.isDragging = False
        self.contentx = self.content.x1
        self.contenty = self.content.y1

    def draw(self,canvas,mask = None):
        # This widget doesn't use mask
        # Because its contents might not be controlled by mask
        # So it has to cover everything else
        super().draw(canvas)
        self.content.draw(canvas,self)
        for item in self.cover:
            item.draw(canvas)

class DrawWindow(GUI_Rect):
    def __init__(self,x1,y1,x2,y2,drawfunc = lambda x,y,z:42,
        color = "white",border = 0, parent = WORLD):
        super().__init__(x1,y1,x2,y2,color,border,parent)
        self.drawfunc = drawfunc

    def draw(self,canvas,mask = None):
        super().draw(canvas,mask)
        self.drawfunc(canvas,self.x1,self.y1)

class InputField(GUI_Rect):

    def __init__(self, x1, y1, x2, y2, 
        color = "white", border = 1, parent = WORLD, maxCharacters = 15):
        self.margin = 5
        self.string = ""
        self.pointer = 0
        self.maxCharacters = maxCharacters
        super().__init__(x1,y1,x2,y2,color,border,parent)

    def keyPressed(self,event):
        if ((event.keysym in string.ascii_letters
            or event.keysym in string.digits 
            or event.keysym == "space" or event.keysym == "#") 
            and len(self.string) < self.maxCharacters):
            if event.keysym == "space":
                # I'm pretty sure there's a better way of doing this 
                # but I'm too lazy to google it
                key = " "
            else: key = event.keysym
            self.string = (self.string[:self.pointer] + key
             + self.string[self.pointer:])
            self.pointer += 1
        if event.keysym == "BackSpace" and self.pointer > 0:
            if len(self.string) > 0:
                self.string = (self.string[:self.pointer - 1]
                + self.string[self.pointer:])
                self.pointer -= 1
        elif event.keysym == "Left":self.pointer -= 1
        elif event.keysym == "Right":self.pointer += 1
        if self.pointer < 0:
            self.pointer = 0
        elif self.pointer > len(self.string):
            self.pointer = len(self.string)

    def draw(self, canvas, mask = None):
        super().draw(canvas)
        x1,y1 = self.getPos()
        string = (self.string[:self.pointer]
            + "_" + self.string[self.pointer:])
        canvas.create_text(x1 + self.margin, y1 + self.margin,
                        text = string, font = "CenturyGothic 15",
                        anchor = "nw")

    def clear(self):
        self.string = ""
        self.pointer = 0

class MessageBox(GUI_Rect):

    INPUT_HEIGHT = 30
    YACTIVE = LIGHTBLUE
    NACTIVE = LIGHTBLUE

    def __init__(self, x1, y1, x2, y2, inputFunc = lambda:42,
        color = "grey", border = 1, parent = WORLD, prompt = ""):
        super().__init__(x1,y1,x2,y2,color,border,parent)
        self.prompt = prompt
        self.margin = 10
        self.isVisible = False
        self.inputFunc = inputFunc
        self.input = InputField(self.margin, self.height / 2 - 30,
                                self.width - self.margin,
                                self.height / 2, parent = self)
        self.yBtn = Button(self.width / 5, self.height * 2 / 3,
                           self.width * 2 / 5, self.height * 5 / 6, text = "Ok",
                           func = self.ok,activeFill = MessageBox.NACTIVE)
        self.nBtn = Button(self.width * 3 / 5, self.height * 2 / 3,
                           self.width * 4 / 5, self.height * 5 / 6, 
                           text = "Cancel",
                           func = self.cancel,activeFill = MessageBox.NACTIVE)
        self.addGUIItem(self.yBtn)
        self.addGUIItem(self.nBtn)
        self.addGUIItem(self.input)

    def ok(self):
        self.inputFunc(self.input.string)
        self.deActivate()

    def activate(self):
        self.isVisible = True

    def deActivate(self):
        self.isVisible = False
        self.input.clear()

    def cancel(self):
        self.deActivate()

    def keyPressed(self,event):
        if not self.isVisible: return
        if event.keysym == "Return":
            self.ok()
        else:
            self.input.keyPressed(event)

    def draw(self,canvas,mask = None):
        if not self.isVisible: return
        super().draw(canvas,mask)
        x1,y1 = self.getPos()
        canvas.create_text(x1 + self.margin, y1 + self.margin,
                           font = "CenturyGothic 18",
                           text = self.prompt, anchor = "nw")

def bar():
    print(42)

class Test(Animation):
    def __init__(self):
        buttons = [{"text":"Haha","border":1}] * 4
        self.s = Selection(10,10,100,100,5,buttons,border = 1)
        self.scroller = Scroller(100,10,110,210,150)
        self.sWindow = SelectionWindow(20,50,300,400,border = 1)
        self.input = InputField(50,50,200,100)
        self.msgBox = MessageBox(20,50,300,400,self.printSth,prompt = "Hahaha")
        self.msgBox.activate()
        for i in range(25):
           self.sWindow.addItem("Matt",lambda:print(123))
        #self.drag = DragWindow(20,50,100,100,self.sWindow)
        self.run(600,600)

    def printSth(self,string):
        print(string)

    def redrawAll(self):
        self.s.draw(self.canvas)
        self.msgBox.draw(self.canvas)
        #self.scroller.draw(self.canvas)
        #self.drag.draw(self.canvas)

    def mouseMotion(self,event):pass
        #self.scroller.onMousemove(event.x,event.y)
        #self.drag.onMouseMove(event.x,event.y)

    def mousePressed(self,event):
        self.s.onMouseDown(event.x,event.y)
        self.msgBox.onMouseDown(event.x,event.y)
        #self.scroller.onMouseDown(event.x,event.y)
        #self.drag.onMouseDown(event.x,event.y)

    def keyPressed(self,event):
        self.input.keyPressed(event)
        self.msgBox.keyPressed(event)

    def leftMouseReleased(self,event):pass
        #self.scroller.onMouseUp(event.x,event.y)
        #self.drag.onMouseUp(event.x,event.y)

#t = Test()
        

