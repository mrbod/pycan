#!/usr/bin/env python
import os
import Tkinter as tk
import tkMessageBox
import tkFileDialog
import threading
import time
import Queue
import random
import canchannel
import kvaser
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
        self.changed = False
        self.scroll()

    def save(self, filename):
        self.info(None, 'Save: ' + filename)
        self.changed = False

    def scroll(self):
        if self.auto_scroll.get():
            self.text.see(tk.END)
        self.after(300, self.scroll)

    def info(self, row, m):
        self.text.insert(tk.END, "{0}\n".format(str(m)))

    def log(self, m):
        self.changed = True
        self.row += 1
        self.text.insert(tk.END, "{1:5d}: {0}\n".format(str(m), self.row))

class PyCan(tk.Tk):
    def __init__(self, channel=0):
        tk.Tk.__init__(self)
        self.channel = channel
        self.title('PyCAN')
        self.menu()
        # text view
        self.logger = Logger(self)
        self.logger.pack(expand=True, fill="both")
        # buttons
        bf = tk.Frame(self)
        bf.pack(side=tk.BOTTOM)
        b = tk.Button(bf, text="send", command=self.send)
        b.pack(side=tk.LEFT)
        auto_scr = self.logger.auto_scroll
        p = tk.Checkbutton(bf, text="Autoscroll" , variable=auto_scr)
        p.pack(side=tk.LEFT)
        self.idfmt = tk.IntVar()
        p = tk.Checkbutton(bf, text="StCAN"
                , variable=self.idfmt
                , onvalue=canmsg.FORMAT_STCAN, offvalue=canmsg.FORMAT_STD
                , command=self.id_format)
        p.pack(side=tk.LEFT)
        self.idfmt.set(canmsg.FORMAT_STD)
        self.channel_setup()
        self.poll()

    def channel_setup(self):
        try:
            driver = kvaser.KvaserCanChannel(channel=self.channel, logger=self.logger)
        except:
            driver = canchannel.CanChannel(logger=self.logger)
        self.logger.info(None, str(driver))
        self.logger.info(None, os.getcwd())
        self.driver = driver

    def menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)
        filemenu = tk.Menu(menu)
        menu.add_cascade(label='File', underline=0, menu=filemenu)
        filemenu.add_command(label='Save', underline=0,
                accelerator='Ctrl-S', command=self.do_save)
        self.bind('<Control-s>', self.do_save)
        filemenu.add_command(label='Exit', underline=1,
                accelerator='Ctrl-Q', command=self.do_quit)
        self.bind('<Control-q>', self.do_quit)

    def do_save(self):
        fn = tkFileDialog.asksaveasfilename(initialdir=os.getcwd())
        self.logger.save(fn)

    def send(self):
        m = canmsg.CanMsg()
        m.addr = 60
        m.group = canmsg.GROUP_PIN
        m.type = canmsg.TYPE_IN
        m.data = [8,7,6,5,4,3,2,1]
        self.driver.write(m)

    def id_format(self):
        canmsg.format_set(self.idfmt.get())
        
    def do_quit(self):
        self.driver.close()
        self.quit()

    def poll(self):
        m = self.driver.read()
        while m:
            self.logger.log(m)
            m = self.driver.read()
        self.after(10, self.poll)

def main(channel):
    app = PyCan(channel)
    app.mainloop()

if __name__ == '__main__':
    try:
        ch = int(sys.argv[1])
    except:
        ch = 0
    try:
        main(ch)
    except KeyboardInterrupt:
        pass

