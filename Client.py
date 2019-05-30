from tkinter import *
from tkinter.scrolledtext import *
from tkinter import font as tkFont
from tkinter import filedialog as tkFileDialog
from tkinter import messagebox as tkMessageBox
from tkinter import simpledialog as tkSimpleDialog
import socket
import threading
from diff_match_patch import diff_match_patch

class Client(object):
    def __init__(self,t,host = '127.0.0.1',name = "user"):
        self.t = t
        self.host = host
        self.port = 5555
        self.name = name
        self.client= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.client.connect((self.host,self.port))
        self.text = ''
        self.modtext = ''
        self.l = threading.Lock()
        self.flag = True
        self.tmptext = ''


    def sendData(self,data):
        dmp = diff_match_patch()
        if self.l.acquire(blocking=False) == False:
            print("skip lock")
            patches = dmp.patch_make(data, self.tmptext)
        else:
            print('send lock')
            patches = dmp.patch_make(data, self.t.textWidget.get(1.0,END))
            self.l.release()
        print('send unlock')
        diff = dmp.patch_toText(patches)
        if self.flag == True:
            self.flag = False
        # self.client.send(data.encode())
        self.client.send(diff.encode())

    def recieveData(self):
        while True:
            try:
                data = self.client.recv(8192)
                dmp = diff_match_patch()
                patches = dmp.patch_fromText(data.decode())
            except:
                break
            if data:
                self.tmptext = self.t.textWidget.get(1.0, END)
                self.l.acquire()
                print('recieve lock')
                if self.flag == True:
                    self.text = ''
                    self.flag = False
                else:
                    self.text = self.t.textWidget.get(1.0, END)
                self.modtext, _ = dmp.patch_apply(patches, self.text)

                index = self.t.textWidget.index("insert")
                end_of_text = False
                text_before_index = self.t.textWidget.get(1.0, index)
                text_after_index = self.t.textWidget.get(index, END)
                if not text_after_index.strip():
                    end_of_text = True

                self.t.textWidget.delete(1.0, END)
                self.t.textWidget.insert(END, self.modtext[:-1])
                self.t.currentText = self.t.textWidget.get(1.0, END)
                if self.t.textWidget.search(text_before_index, 1.0, END) == '1.0':
                    self.t.textWidget.mark_set('insert', index)
                else:
                    if not end_of_text:
                        if self.t.textWidget.search(text_after_index, 1.0, END):
                            self.t.textWidget.mark_set("insert", self.t.textWidget.search(text_after_index, 1.0, END))
                        else:
                            self.t.textWidget.mark_set("insert", index)
                    else:
                        self.t.textWidget.mark_set("insert", END)

                if(self.t.programmingMode):
                    self.t.highlightText()
                self.l.release()
                print('receive unlock')
        self.client.close()

    def data(self):
        self.l.acquire()
        ret = self.text
        self.l.release()
        return ret

    def closeClient(self):
        self.client.close()