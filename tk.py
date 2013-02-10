#!/usr/bin/env python
from Tkinter import *
import threading
import time
import Queue
import random
import cdcchannel
import canmsg

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
            time.sleep(0.1 * random.random())

    def read(self):
        if not self.running:
            sys.exit(0)
        try:
            return self.q.get(0)
        except:
            return None

class App(object):
    def __init__(self):
        self.root = Tk()
        # buttons
        bf = Frame(self.root)
        bf.pack(side=BOTTOM)
        self.button = Button(bf, text="QUIT", fg="red", command=self.quit)
        self.button.pack(side=LEFT)
        p = Button(bf, text="Pause", command=self.auto_scroll)
        p.pack(side=LEFT)
        # text view
        frame = Frame(self.root)
        frame.pack(expand=True, fill="both")
        self.iw = Text(frame)
        self.iw.pack(side=LEFT, expand=False, fill="both")
        self.text = Text(frame)
        self.text.pack(side=LEFT, expand=True, fill="both")
        scrbar = Scrollbar(frame)
        scrbar.pack(side=RIGHT, fill=Y)
        scrbar.config(command=self.text.yview)
        self.text.config(yscrollcommand = scrbar.set)
        self.auto_scroll = False
        self.row = 0
        self.ch =  Ch()
        self.root.after(100, self.poll)

    def mainloop(self):
        try:
            self.root.mainloop()
        finally:
            self.end = True

    def auto_scroll(self):
        self.auto_scroll = not self.auto_scroll

    def quit(self):
        self.ch.close()
        self.root.quit()

    def poll(self):
        m = self.ch.read()
        while m:
            self.log(m)
            m = self.ch.read()
        if not self.auto_scroll:
            self.text.see(END)
        self.root.after(100, self.poll)

    def info(self, row, m):
        self.iw.insert(END, "{0}\n".format(str(m)))

    def log(self, m):
        self.row += 1
        self.text.insert(END, "{1:5d}: {0}\n".format(str(m), self.row))

def main():
    app = App()
    app.mainloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

