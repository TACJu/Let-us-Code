from tkinter import *
from tkinter.scrolledtext import *
from eventBasedAnimationClass import EventBasedAnimationClass
from _thread import *
import threading
import socket
import os, time
from tkinter import font as tkFont
from tkinter import filedialog as tkFileDialog
from tkinter import messagebox as tkMessageBox
from tkinter import simpledialog as tkSimpleDialog
import pygments
import pygments.lexers
import pygments.styles
import time
import subprocess
from diff_match_patch import diff_match_patch
from PIL import ImageTk, Image

from Server import Server
from Client import Client

class TextEditor(EventBasedAnimationClass):

    default_width = 1000
    default_height = 20

    langSwitcher = {
        ".py": "Python",
        ".cpp": "C++",
        ".c": "C",
        ".js": "JavaScript",
        ".java": "Java", 
        ".html": "HTML",
        ".css": "CSS",
        ".php": "PHP",
        ".hs": "Haskell",
        ".clj": "Clojure",
        ".coffee": "CoffeeScript",
        ".scpt": "AppleScript",
        ".h": "Objective C",
        ".scm": "Scheme",
        ".rb": "Ruby",
        ".ml": "OCaml",
        ".scala": "Scala"
    }

    @staticmethod
    def readFile(filename, mode="rt"):
        with open(filename, mode) as fin:
            return fin.read()

    @staticmethod
    def writeFile(filename, contents, mode="wt"):
        with open(filename, mode) as fout:
            fout.write(contents)

    def colorIsBlack(self, color):
        # ranks whether a color is nearing black or white
        color = color[1:]
        count = int(color,16)
        if(count<(16**len(color) -1 )/2):
            return True
        return False

    def styleTokens(self,tokenisedText,colorScheme,
                    startIndex,seenlen,seenLines,flag):
        # apply style to tokens in the text
        for token in tokenisedText:
            styleForThisToken = colorScheme.style_for_token(token[0])
            if(styleForThisToken['color']):
                self.currentColor = "#" + styleForThisToken['color'] 
            else:
                if(self.colorIsBlack(colorScheme.background_color)):
                    self.currentColor = "White"
                else: self.currentColor = "Black"
            if(token[1] == "\n"): seenLines += 1
            if(seenLines > 23 and flag): break
            # the '#' is to denote hex value
            textWidget = self.textWidget
            newSeenLen = seenlen + len(token[1])
            textWidget.tag_add(startIndex+"+%dc"%seenlen,
                startIndex+"+%dc"%(seenlen),
                startIndex+"+%dc"%(newSeenLen))
            self.textWidget.tag_config(startIndex+"+%dc"%seenlen,
                foreground = self.currentColor)
            seenlen = newSeenLen

    def highlightText(self,lineCounter = "1",columnCounter = "0",flag = False):
        # highlight text since syntax mode is on
        text = self.currentText.split("\n")
        text = "\n".join(text[int(lineCounter)-1:])
        startIndex = lineCounter + "." + columnCounter
        seenlen, seenLines = 0,0
        tokenisedText = pygments.lex(text, self.lexer)
        if(self.colorScheme):
            colorScheme = pygments.styles.get_style_by_name(self.colorScheme)
        else:
            colorScheme = pygments.styles.get_style_by_name(
                self.defaultColorScheme)
        if(self.colorIsBlack(colorScheme.background_color)):
            self.insertColor = "White"
        else: self.insertColor = "Black"
        self.textWidget.config(background = colorScheme.background_color,
            highlightbackground = colorScheme.highlight_color,
            highlightcolor = colorScheme.highlight_color,
            insertbackground = self.insertColor)
        self.styleTokens(tokenisedText,colorScheme,startIndex,seenlen,
            seenLines, flag)

    def openFile(self):
        # opens a file, also detects whether it is 
        # a program or not
        self.initProgrammingModeAttributes()
        path = tkFileDialog.askopenfilename()
        if(path):
            self.currentFilePath = path
            self.currentFile = os.path.basename(path)
            self.currentText = TextEditor.readFile(path)
            self.textWidget.delete(1.0,END)
            self.textWidget.insert(1.0,self.currentText)
            self.fileExtension = os.path.splitext(path)[1]
            self.root.wm_title("Let's Code! [%s]" % self.currentFile)
            if(self.fileExtension != ".txt" and
                pygments.lexers.guess_lexer_for_filename(
                    "example%s"%self.fileExtension,[])):
                self.programmingMode = True
                self.lexer = pygments.lexers.guess_lexer_for_filename(
                    "example%s"%self.fileExtension,[])
                self.highlightText()

    def saveFile(self):
        if(self.currentFilePath):
            TextEditor.writeFile(self.currentFilePath, self.currentText)

    def saveAs(self):
        # saves a file, automatically adds extension
        path = tkFileDialog.asksaveasfilename()
        if(path):
            TextEditor.writeFile(path, self.currentText)
            self.currentFilePath = path
            self.currentFile = os.path.basename(path)
            self.fileExtension = os.path.splitext(path)[1]
            self.root.wm_title("Let's Code! [%s]" % self.currentFile)

    def newTab(self):
        TextEditor().run()

    def undo(self):
        self.textWidget.edit_undo()

    def redo(self):
        self.textWidget.edit_redo()

    def cut(self):
        if self.textWidget.tag_ranges("sel"):
            self.clipboard = self.textWidget.get("sel.first","sel.last")
            self.textWidget.delete("sel.first","sel.last")
        else:
            self.clipboard = ""

    def copy(self):
        if self.textWidget.tag_ranges("sel"):
            self.clipboard = self.textWidget.get("sel.first","sel.last")

    def paste(self):
        if self.textWidget.tag_ranges("sel"):
            self.textWidget.insert("insert",self.clipboard)

    def resetFontAttribute(self):
        self.textFont = tkFont.Font(family = self.currentTextWidgetFont,
            size = self.fontSize)
        self.textWidget.config(font = self.font)

    def increaseFontSize(self):
        self.fontSize += 2
        self.resetFontAttribute()

    def decreaseFontSize(self):
        self.fontSize -= 2
        self.resetFontAttribute()

    def highlightString(self,searchString):
        lenSearchString = len(searchString) 
        self.textWidget.tag_delete("search")
        self.textWidget.tag_config("search", background = "#FFE792")
        start = 1.0
        while True:
            pos = self.textWidget.search(searchString, start, stopindex = END)
            if(not pos):
                break
            self.textWidget.tag_add("search", pos, pos+"+%dc"%(lenSearchString))
            start = pos + "+1c"

    # search highlight color #FFE792
    def searchInText(self):
        title = "Search"
        message = "Enter word to search for"
        searchString = tkSimpleDialog.askstring(title,message)
        if(searchString == None): return
        self.highlightString(searchString)

    def findAndReplaceInText(self):
        # finds and replaces a word
        title = "Find and replace"
        message = "Enter string to remove"
        stringToRemove = tkSimpleDialog.askstring(title,message)
        if(stringToRemove == None): return
        message = "Enter string to add"
        stringToReplace = tkSimpleDialog.askstring(title, message)
        if(stringToReplace == None): return
        self.currentText = self.currentText.replace(
            stringToRemove, stringToReplace)
        self.textWidget.delete(1.0, END)
        self.textWidget.insert(1.0, self.currentText)
        self.highlightString(stringToReplace)

    def addButton(self, bar, path, func):
        img = ImageTk.PhotoImage(Image.open(path))
        self.imgs.append(img)
        button = Button(bar, image=img, command=func)
        button.pack(side=LEFT)

    def initBtnBar(self):
        self.btnBar = Frame(self.root, width = 400, height = 20)
        self.btnBar.pack(side = TOP, fill = "both", expand = "True")
        self.imgs = []
        self.addButton(self.btnBar, "./icons/new.png", self.newTab)
        self.addButton(self.btnBar, "./icons/open.png", self.openFile)
        self.addButton(self.btnBar, "./icons/save.png", self.saveFile)
        self.addButton(self.btnBar, "./icons/saveas.png", self.saveAs)
        self.addButton(self.btnBar, "./icons/undo.png", self.undo)
        self.addButton(self.btnBar, "./icons/redo.png", self.redo)
        self.addButton(self.btnBar, "./icons/play.png", self.runCode)
        self.teamInfo = Label(self.btnBar, text="      Let's Code! —— 协同代码编辑器，由509寝室一群爱一起码代码的好基友开发")
        self.teamInfo.pack(side="left")

    def initTextWidget(self):
        self.textWidgetContainer = Frame(self.root, width = 400, height = 400)
        self.textWidgetContainer.grid_propagate(False)
        self.textWidgetContainer.pack(side = TOP, fill = "both", expand = True)
        self.textWidgetContainer.grid_rowconfigure(0, weight=1)
        self.textWidgetContainer.grid_columnconfigure(0, weight=1)
        self.textWidget = ScrolledText(self.textWidgetContainer, 
            width = 10,
            font = self.textFont,
            background =self.textWidgetBackGround)
        self.textWidget.grid(row = 0, column = 0, sticky = "nsew")
        self.textWidget.config(insertbackground = self.cursorColor,
            foreground = self.textWidgetDefaultFontColor,
            tabs = ("%dc"%self.tabWidth,"%dc"%(2*self.tabWidth)),
            undo = True)

    def initConsole(self):
        self.consoleContainer = Frame(self.root, width = 400, height = 150)
        self.consoleContainer.grid_propagate(False)
        self.consoleContainer.pack(side = TOP, fill = "both", expand = True)
        self.consoleContainer.grid_rowconfigure(0, weight=1)
        self.consoleContainer.grid_columnconfigure(0, weight=1)
        self.console = ScrolledText(self.consoleContainer, 
            width = 10,
            font = self.consoleFont,
            background = self.consoleBackGround,
            foreground = self.consoleDefaultFontColor)
        self.console.grid(row = 0, column = 0, sticky = "nsew")
        self.console.config(state=DISABLED)

    def activateConsole(self):
        self.consoleContainer.pack(side = TOP, fill = "both", expand = True)

    def deactivateConsole(self):
        self.consoleContainer.pack_forget()

    def runCode(self):
        if not self.currentFilePath:
            self.saveAs()
        else:
            self.saveFile()
        cmd = []
        if self.fileExtension == ".py":
            cmd.append("python3")
        elif self.fileExtension == ".js":
            cmd.append("node")
        else:
            return
        self.activateConsole()
        cmd.append(self.currentFilePath)
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.console.config(state=NORMAL)
        self.console.delete('1.0','end')
        self.console.insert(END, output)
        self.console.insert(END, errors)
        self.console.config(state=DISABLED)

    def initFont(self):
        self.currentTextWidgetFont = "Monaco"
        self.currentConsoleFont = "Courier"
        self.fontSize = 15
        self.consoleFontSize = 15
        self.textFont = tkFont.Font(family = self.currentTextWidgetFont, 
            size = self.fontSize)
        self.consoleFont = tkFont.Font(family = self.currentConsoleFont,
            size = self.consoleFontSize)

    def initProgrammingModeAttributes(self):
        self.programmingMode = False
        self.colorScheme = None
        self.defaultColorScheme = "monokai"
        self.lexer = None

    def initMoreGeneralAttributes(self):
        self.hostingServer = False
        self.hostIP = None
        self.joinedServerIP = None
        self.server = None
        self.client = None
        self.root.wm_title("Let's Code! [Untitled]")

    def initGeneralAttributes(self):
        # general editor attributes
        self.currentText,self.tabWidth = "",1
        self.rulerWidth,self.currentFilePath = None,None
        self.currentFile = None
        self.fileExtension = None
        self.indentationLevel = 0
        self.prevChar = None
        self.clipboard = ""
        self.collaborativeCodingMode = False
        self.insertColor = "Black"
        self.initMoreGeneralAttributes()

    def initTextWidgetAttributes(self):
        self.textWidgetBackGround = "White"
        self.textWidgetDefaultFontColor = "Black"
        self.textWidgetTabSize = ""
        self.cursorColor = "Black"

    def initConsoleAttributes(self):
        self.consoleBackGround = "Black"
        self.consoleDefaultFontColor = "White"

    def initAttributes(self):
        self.initGeneralAttributes()
        self.initFont()
        self.initProgrammingModeAttributes()
        self.initTextWidgetAttributes()
        self.initConsoleAttributes()

    def addEditMenu(self):
        self.editMenu = Menu(self.menuBar, tearoff = 0)
        self.editMenu.add_command(label = "Undo", command = self.undo)
        self.editMenu.add_command(label = "Redo", command = self.redo)
        self.editMenu.add_command(label = "Cut", command = self.cut)
        self.editMenu.add_command(label = "Copy", command = self.copy)
        self.editMenu.add_command(label = "Paste", command = self.paste)
        self.editMenu.add_command(label = "Increase Font", 
            command = self.increaseFontSize)
        self.editMenu.add_command(label = "Decrease Font", 
            command = self.decreaseFontSize)
        self.menuBar.add_cascade(label = "Edit", menu = self.editMenu)

    def addFileMenu(self):
        self.fileMenu = Menu(self.menuBar, tearoff = 0)
        self.fileMenu.add_command(label = "Open", command = self.openFile)
        self.fileMenu.add_command(label = "New File", command = self.newTab)
        self.fileMenu.add_command(label = "Save", command = self.saveFile)
        self.fileMenu.add_command(label = "Save As", command = self.saveAs)
        self.menuBar.add_cascade(label = "File", menu = self.fileMenu)

    def setFileExtension(self, ext):
        # sets file extension
        self.fileExtension = ext
        self.programmingMode = True
        try:
            self.lexer = pygments.lexers.guess_lexer_for_filename("example%s"%self.fileExtension,[])
        except:
            self.lexer = pygments.lexers.guess_lexer_for_filename("example.py",[])
        self.highlightText()

    def setColorScheme(self, colorScheme):
        self.colorScheme = colorScheme
        self.programmingMode = True
        # assumes start from python
        if(not self.lexer):
            self.lexer = pygments.lexers.guess_lexer_for_filename("example.py",[])
            self.fileExtension = ".py"
        self.highlightText()

    def addColorSchemeCommand(self, name):
        self.colorSchemeMenu.add_command(label = name,
                command = lambda : self.setColorScheme(name))

    def addColorSchemeMenu(self):
        # colorScheme Menu
        self.colorSchemeMenu = Menu(self.menuBar, tearoff = 0)
        self.addColorSchemeCommand("manni")
        self.addColorSchemeCommand("igor")
        self.addColorSchemeCommand("xcode")
        self.addColorSchemeCommand("vim")
        self.addColorSchemeCommand("autumn")
        self.addColorSchemeCommand("vs")
        self.addColorSchemeCommand("rrt")
        self.addColorSchemeCommand("native")
        self.addColorSchemeCommand("perldoc")
        self.addColorSchemeCommand("borland")
        self.addColorSchemeCommand("tango")
        self.addColorSchemeCommand("emacs")
        self.addColorSchemeCommand("friendly")
        self.addColorSchemeCommand("monokai")
        self.addColorSchemeCommand("paraiso-dark")
        self.addColorSchemeCommand("colorful")
        self.addColorSchemeCommand("murphy")
        self.addColorSchemeCommand("bw")
        self.addColorSchemeCommand("pastie")
        self.addColorSchemeCommand("paraiso-light")
        self.addColorSchemeCommand("trac")
        self.addColorSchemeCommand("default")
        self.addColorSchemeCommand("fruity")
        self.menuBar.add_cascade(label = "Color Scheme",
            menu = self.colorSchemeMenu)

    def addLanguageCommand(self, language, extension):
        self.syntaxMenu.add_command(label = language, 
            command = lambda : self.setFileExtension(extension))

    def addSyntaxMenu(self):
        self.syntaxMenu = Menu(self.menuBar, tearoff = 0)
        self.addLanguageCommand("Python",".py")
        self.addLanguageCommand("C++",".cpp")
        self.addLanguageCommand("C", ".c")
        self.addLanguageCommand("JavaScript",".js")
        self.addLanguageCommand("Java",".java")
        self.addLanguageCommand("HTML",".html")
        self.addLanguageCommand("CSS",".css")
        self.addLanguageCommand("PHP",".php")
        self.addLanguageCommand("Haskell",".hs")
        self.addLanguageCommand("Clojure",".clj")
        self.addLanguageCommand("CoffeeScript",".coffee")
        self.addLanguageCommand("AppleScript",".scpt")
        self.addLanguageCommand("Objective C",".h")
        self.addLanguageCommand("Scheme",".scm")
        self.addLanguageCommand("Ruby",".rb")
        self.addLanguageCommand("OCaml",".ml")
        self.addLanguageCommand("Scala",".scala")
        self.viewMenu.add_cascade(label = "Syntax", menu = self.syntaxMenu)
        self.menuBar.add_cascade(label = "View", menu = self.viewMenu)

    def addViewMenu(self):
        self.viewMenu = Menu(self.menuBar, tearoff = 0)
        # syntax Menu
        self.addSyntaxMenu()
        self.addColorSchemeMenu()

    def addDebugMenu(self):
        self.runMenu = Menu(self.menuBar, tearoff = 0)
        self.runMenu.add_command(label = "Show Console", command = self.activateConsole)
        self.runMenu.add_command(label = "Hide Console", command = self.deactivateConsole)
        self.runMenu.add_command(label = "Run", command = self.runCode)
        self.menuBar.add_cascade(label = "Debug", menu = self.runMenu)

    def displayMessageBox(self, title = "", text = ""):
        tkMessageBox.showinfo(title, text)

    def startServer(self):
        # starts a new thread running the server
        self.collaborativeCodingMode = True
        start_new_thread(self.server.acceptConnection(),())

    def startRecieving(self):    
        # starts a new thread to recieve data
        start_new_thread(self.client.recieveData,())

    def collaborateWrapper(self):
        # starts collaborative mode
        if(not self.collaborativeCodingMode):
            self.server = Server(self)
            host = self.server.getHost()
            self.hostingServer = True
            self.hostIP = host
            self.client = Client(self, host)
            start_new_thread(self.startServer,())
            start_new_thread(self.startRecieving,())
            time.sleep(.01)

    def joinServer(self):
        # starts a new thread to recieve data
        start_new_thread(self.client.recieveData,())

    def joinServerWrapper(self):
        # join a server for collaboration
        if(not self.collaborativeCodingMode):
            try:
                self.collaborativeCodingMode = True
                title = "Host IP address"
                message = "Enter IP address of server to link to."
                host = tkSimpleDialog.askstring(title,message)
                if(host == None): 
                    self.collaborativeCodingMode = False
                    return       
                self.joinedServerIP = host
                self.client = Client(self, host)
                start_new_thread(self.joinServer,())
            except:
                self.collaborativeCodingMode = False
                self.joinedServerIP = None
                print("Server isn't running")
                self.displayMessageBox("Error","Server isn't running")

    def addNetworkMenu(self):
        self.networkMenu = Menu(self.menuBar, tearoff = 0)
        self.networkMenu.add_command(label = "Create new server", 
                                    command = self.collaborateWrapper)
        self.networkMenu.add_command(label = "Join server", 
                                    command = self.joinServerWrapper)
        self.menuBar.add_cascade(label = "Collaborate", 
                                menu = self.networkMenu)
        
    def addFindMenu(self):
        self.findMenu = Menu(self.menuBar, tearoff = 0)
        self.findMenu.add_command(label = "Search", command =self.searchInText)
        self.findMenu.add_command(label = "Find and Replace", 
            command = self.findAndReplaceInText)
        self.menuBar.add_cascade(label = "Find", menu = self.findMenu)

    def showHelp(self):
        self.helpCanvasRoot = Tk()
        self.helpCanvas = Canvas(self.helpCanvasRoot, width = 600, height = 600)
        self.helpCanvasRoot.wm_title("Let's Code! | Help")
        self.helpCanvas.pack()
        canvas = self.helpCanvas
        canvas.create_rectangle(0,0,600,600,fill="Grey")
        canvas.create_text(300,30,text = "Let's Code!", 
            font = "Arial 30 bold italic underline")
        canvas.create_rectangle(8,48,592,596,fill = "White",
            width = 2)
        message = """
        1. Find all options on the top of the screen in the menu bar.
        2. To enable syntax highlighting choose the programming 
            language in View --> Syntax menu.
        3. Choose the color scheme you want in the color
            scheme menu.
        4. To collaborate with others you can either start a server
            or join a server
                1. To start a server click 
                    Collaboration --> Start New Server
                    This will display your IP address in the 
                    bottom which your friend will join.
                2. To join click Collaboration --> Join Server
                    Enter server IP you want to join
                    and click OK.
        """
        canvas.create_text(10,50,text = message, anchor = "nw",
            fill = "Dark Blue", font = "Arial 18 bold")
        canvas.mainloop()

    def showAbout(self):
        self.aboutCanvasRoot = Tk()
        self.aboutCanvas = Canvas(self.aboutCanvasRoot, width = 1200,height =670)
        self.aboutCanvasRoot.wm_title("Let's Code! | About")
        self.aboutCanvas.pack()
        self.aboutCanvas.create_rectangle(0,0,1200,670,fill="Grey")
        self.aboutCanvas.create_text(300,30,text = "Let's Code!", 
            font = "Arial 30 bold italic underline")
        self.aboutCanvas.create_rectangle(30,48,1100,652,fill = "White",
            width = 2)
        message = """
        This is a collaborative code editor developed by Ju He, Dongwei Xiang
        , XU Song and Yuzhang Hu. This project beblongs to the project of the course:
        "Intoduction to the Network" in Peking University in the spring semester, 2019.
        We offer this program with the name "Let's Code", which means that we encourage 
        everyone to be envolved in coding. Just like its name, you can cooperate with 
        your teammates to code one source file at the same time. Sounds exciting, isn't it? 
        To do this is extremely easy with our program. What your need to do is only to click 
        the "Collaborative" tag and create a new server. Then your friends can 
        use the IP to connect to your session and begin to work together with you.
        What's more, we provide other tools which may contribute to your work. For 
        example, we support many kinds of programming languages  like C++, Python or so, 
        and will be kept updating since now. Besides, you can even run the code after finish 
        editing it. Right now we only support python code with Python3 and JavaScript code 
        with Node, more languages' supportment is under development.
        As is known to all, the best way to learn to use a program is to try it by 
        yourself. What we describe is just a small part of our work. So explore it as you like and 
        hope you will enjoy it!
        To contact with us, send email to "yuzhnaghu@pku.edu.cn"
        """
        self.aboutCanvas.create_text(10,50,text = message, anchor = "nw",
            fill = "Dark Blue", font = "Arial 18 bold")
        self.aboutCanvasRoot.mainloop()

    def addHelpMenu(self):
        self.helpMenu = Menu(self.menuBar, tearoff = 0)
        self.helpMenu.add_command(label = "Help", command = self.showHelp)
        self.helpMenu.add_command(label = "About", command = self.showAbout)
        self.menuBar.add_cascade(label = "Help", menu = self.helpMenu)

    def initMenuBar(self):
        # init menuBar
        self.menuBar = Menu(self.root)
        # file menu option
        self.addFileMenu()
        # Edit menu option
        self.addEditMenu()
        # Find menu option
        self.addFindMenu()
        # View menu option
        self.addViewMenu()
        # Network menu
        self.addNetworkMenu()
        # Debug menu
        self.addDebugMenu()
        # Help menu
        self.addHelpMenu()
        self.root.config(menu = self.menuBar)

    def onTabPressed(self, event):
        if(self.fileExtension == ".py"):
            self.indentationLevel += 1

    def onWindowResized(self, event):
        self.width = event.width

    def bindEvents(self):
        self.textWidget.bind("<Tab>",lambda event: self.onTabPressed(event))
        self.root.bind("<Configure>", self.onWindowResized)

    def indent(self):
        if(self.fileExtension == ".py"):
            self.textWidget.insert("insert","\t"*self.indentationLevel)

    def modifyIndent(self, event):
        # modifies indentation based on python rules
        if(self.fileExtension == ".py"):
            if(event.char == ":"): 
                self.indentationLevel += 1
            elif(event.keysym == "BackSpace"):
                line = self.textWidget.get("insert linestart","insert lineend")
                flag = True
                for c in line:
                    if not((c == " ") or (c == "\t")):
                        flag = False
                        break
                if(flag):
                    self.indentationLevel = (self.indentationLevel - 1 if 
                        self.indentationLevel>=1 else 0)

    def completeParens(self, event):
        # autocomplete parens
        if(event.char == "{" and self.programmingMode):
            self.textWidget.insert("insert","\n"+"\t"*self.indentationLevel+"}")
            self.currentText = self.textWidget.get(1.0,END)
            posStr = self.textWidget.index(INSERT)
            pointPos = posStr.index(".")
            lineStr = posStr[0:pointPos]
            rowStr = posStr[pointPos + 1:]
            rowStr = str(int(rowStr) - 1)
            self.textWidget.mark_set(INSERT, lineStr + "." + rowStr)
        elif(event.char == "(" and self.programmingMode):
            self.textWidget.insert("insert",")")
            self.currentText = self.textWidget.get(1.0,END)
            posStr = self.textWidget.index(INSERT)
            pointPos = posStr.index(".")
            lineStr = posStr[0:pointPos]
            rowStr = posStr[pointPos + 1:]
            rowStr = str(int(rowStr) - 1)
            self.textWidget.mark_set(INSERT, lineStr + "." + rowStr)

    def getLineAndColFromIndex(self, index):
        return int(index.split('.')[0]),int(index.split('.')[1])

    def onKeyPressed(self, event):
        ctrl  = ((event.state & 0x0004) != 0)
        shift = ((event.state & 0x0001) != 0)
        command = ((event.state & 0x0008) != 0)
        flag = False
        if(self.textWidget.get(1.0,END)!=self.currentText):
            flag = True
            tmpText = self.currentText
        if(event.keysym == "Return" and self.fileExtension == ".py"):
            self.indent()
        self.modifyIndent(event)
        self.completeParens(event)
        if (flag):
            dmp = diff_match_patch()
            patches = dmp.patch_make(tmpText, self.textWidget.get(1.0,END))
            diff = dmp.patch_toText(patches)
        self.currentText = self.textWidget.get(1.0,END)
        if((flag) and self.collaborativeCodingMode):
            # print(diff)
            self.client.sendData(tmpText)
            # self.client.sendData(diff)
        if(self.programmingMode):
            if((command and event.keysym in "vV")):
                self.highlightText()
            else:
                insertLineNumber = int(self.textWidget.index(
                                                    "insert").split(".")[0])
                self.highlightText(
                        str(insertLineNumber),"0", 
                        (event.keysym!="Return" and 
                        not self.collaborativeCodingMode)
                        ) 
        if(self.fileExtension == ".py" and command and event.keysym in "bB"):
            self.compilePythonCode()

    def onMousePressed(self, event):
        # remove search tag if it exists
        self.textWidget.tag_delete("search")

    def onTimerFired(self):
        pass

    def redrawAll(self):
        # draws info onto canvas
        self.canvas.delete(ALL)
        self.canvas.create_rectangle(0,0,self.width,self.height,fill = "#672678", outline="")
        # show programming language
        if(self.programmingMode):
            self.canvas.create_text(self.width / 3, 10,
                text = "Lang: " + self.langSwitcher[self.fileExtension],fill = "White")
        # show current cursor
        a = self.textWidget.index("insert")
        ln = int(a.split(".")[0])
        l = self.textWidget.get("insert linestart","insert")
        cn = 1
        for c in l:
            if(c == "\t"):
                cn += 4*self.tabWidth
            else:
                cn += 1
        self.canvas.create_text(60, 10, text="Row: %d Column: %d"%(ln,cn),
                                fill = "White")
        # show server&client host
        if(self.hostingServer):
            self.canvas.create_text(self.width * 2 / 3 - 20, 10,
                text = "Hosting server at IP: %s"%(self.hostIP),fill = "White")
        elif(self.joinedServerIP):
            self.canvas.create_text(self.width * 2 / 3 - 20, 10,
                text = "Joined server at IP: %s"%(self.joinedServerIP), fill = "White")
        
        # show time
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.canvas.create_text(self.width - 75, 10,
                text = timestr, fill = "White")

        
    def initAnimation(self):
        self.timerCounter = 250
        self.initAttributes()
        self.initBtnBar()
        self.initTextWidget()
        self.initConsole()
        self.initMenuBar()
        self.bindEvents()

    def __init__(self, width=0, height=0):
        if width == 0:
            self.width = TextEditor.default_width
        if height == 0:
            self.height = TextEditor.default_height
        super(TextEditor, self).__init__(self.width, self.height)