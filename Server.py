from tkinter import *
from tkinter.scrolledtext import *
from tkinter import font as tkFont
from tkinter import filedialog as tkFileDialog
from tkinter import messagebox as tkMessageBox
from tkinter import simpledialog as tkSimpleDialog
import socket
from threading import _start_new_thread
from diff_match_patch import diff_match_patch

class Server(object):
    def __init__(self,t,port = 5555):
        self.t = t
        self.port = port
        self.text = ""      
        self.host = socket.gethostbyname(socket.gethostname())
        print(self.host," is host")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))
        self.s.listen(2)
        self.connections = []

    def getHost(self):
        return self.host

    def threaded_client(self,conn):
        # conn.send("Connected to server\n")
        while True:
            try:
                data = conn.recv(8192)
            except:
                data = ""
            if(not data):
                break
            # conn.sendall(reply)
            for c,a in self.connections:
                try:
                    if c != conn:
                        c.sendall(data)
                except:
                    print("connection lost")
                    self.connections.remove((c,a))
        conn.close()

    def acceptConnection(self):
        while True:
            conn, addr = self.s.accept()
            dmp = diff_match_patch()
            patches = dmp.patch_make('', self.t.textWidget.get(1.0,END))
            diff = dmp.patch_toText(patches)
            conn.send(diff.encode())
            self.connections += [(conn,addr)]
            _start_new_thread(self.threaded_client,(conn,))