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
        self.button = Button(bf, text="Quit", fg="red", command=self.quit)
        self.button.pack(side=LEFT)
        p = Button(bf, text="Pause", command=self.auto_scroll)
        p.pack()
        frame = Frame(master)
        frame.pack(expand=True, fill="both")
        self.text = Text(frame)
        self.text.pack(side=LEFT, expand=True, fill="both")
        scrbar = Scrollbar(frame)
        scrbar.pack(side=RIGHT, fill=Y)
        scrbar.config(command=self.text.yview)
        self.text.config(yscrollcommand = scrbar.set)
        self._auto_scroll = False
        self.row = 0
        self.ch = cdcchannel.CDCChannel(0, "localhost", 5555)
        self.ch.logger = self
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
        self.master.after(500, self.poll)

    def info(self, row, m):
        self.text.insert(END, "{0}\n".format(str(m)))

    def log(self, m):
        self.row += 1
        self.text.insert(END, "{1:5d}: {0}\n".format(str(m), self.row))

def main():
    root = Tk()
    app = App(root)
    try:
        root.mainloop()
    finally:
        app.end = True
    sys.exit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

