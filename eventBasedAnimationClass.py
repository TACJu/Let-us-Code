from tkinter import *

class EventBasedAnimationClass(object):
    def onMousePressed(self, event): pass
    def onKeyPressed(self, event): pass
    def onTimerFired(self): pass
    def redrawAll(self): pass
    def initAnimation(self): pass

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.timerDelay = 250

    def onMousePressedWrapper(self, event):
        self.onMousePressed(event)
        self.redrawAll()

    def onKeyPressedWrapper(self, event):
        self.onKeyPressed(event)
        self.redrawAll()

    def onTimerFiredWrapper(self):
        if (self.timerDelay == None):
            return
        self.onTimerFired()
        self.redrawAll()
        self.canvas.after(self.timerDelay, self.onTimerFiredWrapper)         

    def run(self):
        self.root = Toplevel()
        self.canvas = Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack(side = BOTTOM,anchor = "nw")
        self.initAnimation()
        def f(event): self.onMousePressedWrapper(event)    
        self.root.bind("<Button-1>", f)
        self.root.bind("<Key>", lambda event: self.onKeyPressedWrapper(event))
        self.onTimerFiredWrapper()
        self.root.mainloop()