#!/usr/bin/env python
import Tkinter as tk
import tkMessageBox as mb
import threading
import time
import Queue
import random
import canchannel
import canmsg

channels = ('kvaser', 'canchannel')

class Logger(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master=master)
        self.text = tk.Text(self)
        self.text.pack(side=tk.LEFT, expand=True, fill="both")
        scrbar = tk.Scrollbar(self)
        scrbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrbar.config(command=self.text.yview)
        self.text.config(yscrollcommand = scrbar.set)
        self.row = 0
        self.auto_scroll = tk.IntVar()
        self.auto_scroll.set(1)

    def info(self, row, m):
        self.text.insert(tk.END, "{0}\n".format(str(m)))

    def log(self, m):
        self.row += 1
        self.text.insert(tk.END, "{1:5d}: {0}\n".format(str(m), self.row))
        if self.auto_scroll.get():
            self.text.see(tk.END)

class PyCan(tk.Tk):
    def __init__(self, channel):
        tk.Tk.__init__(self)
        self.title('PyCAN')
        # text view
        self.logger = Logger(self)
        self.logger.pack(expand=True, fill="both")
        # buttons
        bf = tk.Frame(self)
        bf.pack(side=tk.BOTTOM)
        self.button = tk.Button(bf, text="QUIT", fg="red", command=self.do_quit)
        self.button.pack(side=tk.LEFT)
        p = tk.Checkbutton(bf, text="Autoscroll"
                , variable=self.logger.auto_scroll)
        p.pack(side=tk.LEFT)
        self.idfmt = tk.IntVar()
        p = tk.Checkbutton(bf, text="StCAN"
                , variable=self.idfmt
                , onvalue=canmsg.FORMAT_STCAN, offvalue=canmsg.FORMAT_STD
                , command=self.id_format)
        p.pack(side=tk.LEFT)
        self.idfmt.set(canmsg.FORMAT_STD)
        self.ch = channel
        self.ch.logger = self.logger
        self.after(100, self.poll)

    def id_format(self):
        canmsg.format_set(self.idfmt.get())
        
    def do_quit(self):
        if not mb.askyesno('Hehe', 'Sure?'):
            return
        self.ch.close()
        self.quit()

    def poll(self):
        m = self.ch.read()
        while m:
            self.logger.log(m)
            m = self.ch.read()
        self.after(100, self.poll)

def main():
    c = canchannel.CanChannel()
    app = PyCan(c)
    app.mainloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

