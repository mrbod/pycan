#!/usr/bin/env python
import time
import canmsg
import threading

class CanChannel(object):
    def __init__(self):
        self.starttime = time.time()
        self.T0 = self.gettime()
        self._write_lock = threading.Lock()
        self.logger = None
        self.read_cnt = 0
        self.write_cnt = 0
    
    def open(self):
        self.starttime = time.time()

    def close(self):
        self.log('duration %.3fs' % self.gettime())

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time() - self.starttime

    def do_read(self):
        T = self.gettime()
        if T - self.T0 > 2:
            self.T0 = T
            m = canmsg.CanMsg()
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
        if self.logger != None:
            self.logger.log(x)

    def action_handler(self, key):
        pass

    def message_handler(self, m):
        self.log(str(m))

    def exit_handler(self):
        pass

if __name__ == '__main__':
    import interface
    ch = CanChannel()
    interface = interface.Interface(ch)
    interface.run()

