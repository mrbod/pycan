#!/usr/bin/env python
import sys
import time
from canmsg import CanMsg

class CanChannel(object):
    def __init__(self, on_msg=None):
        self.on_msg = on_msg
        self.starttime = self.gettime()

    def gettime(self):
        return time.time()

    def do_read(self):
        m = CanMsg()
        m.time = self.gettime() - self.starttime
        return m

    def read(self):
        m = self.do_read()
        if m:
            if self.on_msg:
                self.on_msg(m)
        return m

    def do_write(self, msg):
        msg.time = self.gettime() - self.starttime

    def write(self, msg):
        self.do_write(msg)
        msg.sent = True
        if self.on_msg:
            self.on_msg(msg)

def msghandler(m):
    print m

def main():
    ch = CanChannel(msghandler)
    cnt = 0
    while True:
        m = ch.read()
        cnt += 1
        m.id = cnt
        ch.write(m)
        sys.stdout.flush()
        time.sleep(0.9)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

