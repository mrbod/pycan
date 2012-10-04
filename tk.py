#!/usr/bin/env python
from Tkinter import *
import threading
import time
import Queue
import random
#import cdcchannel
#import stcan

class Ch(object):
    def __init__(self):
        self.q = Queue.Queue()
        self.running = True
        thread = threading.Thread(target=self.run)
        thread.start()

    def close(self):
        self.running = False

    def run(self):
        while self.running:
            self.q.put(str(time.time()))
            time.sleep(0.01 * random.random())

    def read(self):
        if not self.running:
            sys.exit(0)
        try:
            return self.q.get(0)
        except:
            return None

class App(object):
    def __init__(self, master):
        self.master = master
        bf = Frame(master)
        bf.pack(side=BOTTOM, fill=Y)
        self.button = Button(bf, text="QUIT", fg="red", command=self.quit)
        self.button.pack(side=LEFT)
        self.hi_there = Button(bf, text="Hello", command=self.say_hi)
        self.hi_there.pack(side=LEFT)
        p = Button(bf, text="Pause", command=self.auto_scroll)
        p.pack(side=LEFT)
        frame = Frame(master)
        frame.pack(expand=True, fill="both")
        self.text = Text(frame)
        self.text.pack(side=LEFT, expand=True, fill="both")
        scrbar = Scrollbar(frame)
        scrbar.pack(side=LEFT, fill=Y)
        scrbar.config(command=self.text.yview)
        self.text.config(yscrollcommand = scrbar.set)
        self._auto_scroll = False
        self.row = 0
        self.ch =  Ch()
        #cdcchannel.CDCChannel(0, "slacker", 5555, msg_class=stcan.StCanMsg)
        self.master.after(100, self.poll)

    def auto_scroll(self):
        self._auto_scroll = not self._auto_scroll

    def quit(self):
        self.ch.close()
        self.master.quit()

    def poll(self):
        m = self.ch.read()
        while m:
            self.log(m)
            m = self.ch.read()
        if not self._auto_scroll:
            self.text.see(END)
        self.master.after(300, self.poll)

    def info(self, row, m):
        self.text.insert(END, "{0}\n".format(str(m)))

    def log(self, m):
        self.row += 1
        self.text.insert(END, "{1:5d}: {0}\n".format(str(m), self.row))

    def say_hi(self):
        self.text.insert(END, "hi there, everyone!\n")

def main():
    root = Tk()
    app = App(root)
    try:
        root.mainloop()
    finally:
        app.end = True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

