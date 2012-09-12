#!/usr/bin/env python
import sys
import time
import canmsg
import threading

class CanChannel(object):
    def __init__(self, msg_class=canmsg.CanMsg):
        self.starttime = time.time()
        self.T0 = self.gettime()
        self._write_lock = threading.Lock()
        self.logger = None
        self.read_cnt = 0
        self.write_cnt = 0
        self.msg_class = msg_class
    
    def open(self):
        self.starttime = time.time()

    def close(self):
        pass

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time() - self.starttime

    def do_read(self):
        T = self.gettime()
        if T - self.T0 > 2:
            self.T0 = T
            m = self.msg_class()
            m.time = T
            return m
        return None

    def read(self):
        m = None
        try:
            m = self.do_read()
        finally:
            pass
        if m:
            self.read_cnt += 1
            m.channel = self
            self.message_handler(m)
        return m

    def do_write(self, msg):
        msg.time = self.gettime()

    def write(self, msg):
        self._write_lock.acquire(True)
        try:
            self.do_write(msg)
        finally:
            self._write_lock.release()
        self.write_cnt += 1
        msg.channel = self
        msg.sent = True
        self.message_handler(msg)

    def info(self, row, x):
        if self.logger != None:
            self.logger.info(row, x)

    def log(self, x):
        if self.logger == None:
            sys.stdout.write(str(x))
            sys.stdout.write('\n')
        else:
            self.logger.log(x)

    def action_handler(self, key):
        pass

    def message_handler(self, m):
        self.log(m)

    def exit_handler(self):
        pass

def main():
    sys.stdout.write('This is the base CAN channel class\n')
    sys.stdout.write('Only emulated CAN message input is provided.\n')
    ch = CanChannel()
    while True:
        m = ch.read()
        if not m:
            time.sleep(0.1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

