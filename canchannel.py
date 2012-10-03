#!/usr/bin/env python
import sys
import time
import canmsg
import threading
import random

class CanChannel(object):
    def __init__(self, msg_class=canmsg.CanMsg):
        self.starttime = time.time()
        self.T0 = self.gettime()
        self._write_lock = threading.Lock()
        self.logger = None
        self.read_cnt = 0
        self.write_cnt = 0
        self.msg_class = msg_class
        self._dT = 0.0
    
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
        if T - self.T0 > self._dT:
            self.T0 = T
            self._dT = 0.5 * random.random()
            m = self.msg_class()
            if random.randint(0,1) == 0:
                m.id = random.randint(0, 2**11 - 1)
            else:
                m.id = random.randint(0, 2**29 - 1)
                m.extended = True
            m.time = T
            dlc = random.randint(0,8)
            m.data = [random.randint(0, 255) for x in range(dlc)]
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
            sys.stdout.flush()
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
            time.sleep(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

