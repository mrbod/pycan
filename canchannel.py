#!/usr/bin/env python
import sys
import time
import threading
import Queue
import random
import canmsg

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
        self.wt = threading.Thread(target=self._writer)
        self.rt = threading.Thread(target=self._reader)
        self.mt = threading.Thread(target=self._message_handler)
        self.wt.daemon = True
        self.rt.daemon = True
        self.mt.daemon = True
        self.wq = Queue.Queue()
        self.rq = Queue.Queue()
        self.mq = Queue.Queue()
        self.running = True
        self.mt.start()
        self.wt.start()
        self.rt.start()
    
    def _writer(self):
        try:
            while self.running:
                try:
                    m = self.wq.get(True, 0.1)
                    self.do_write(m)
                except Queue.Empty:
                    pass
        except Exception, e:
            sys.stderr.write(str(e) + '\n')
            self.close()
            sys.exit()

    def _reader(self):
        try:
            while self.running:
                m = self.do_read()
                if m:
                    self.rq.put(m)
        except Exception, e:
            sys.stderr.write(str(e) + '\n')
            self.close()
            sys.exit()

    def _message_handler(self):
        try:
            while self.running:
                try:
                    m = self.mq.get(True, 0.1)
                    self.message_handler(m)
                except Queue.Empty:
                    pass
        except Exception, e:
            sys.stderr.write(str(e) + '\n')
            self.close()
            sys.exit()

    def open(self):
        self.starttime = time.time()

    def close(self):
        self.running = False

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time() - self.starttime

    def do_read(self):
        T = self.gettime()
        time.sleep(self._dT)
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

    def do_write(self, m):
        m.time = self.gettime()

    def read(self):
        try:
            m = self.rq.get(False)
        except Queue.Empty:
            return None
        self.read_cnt += 1
        m.channel = self
        self.mq.put(m)
        return m

    def write(self, m):
        self.write_cnt += 1
        m.channel = self
        m.sent = True
        self.wq.put(m)
        self.mq.put(m)

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
    try:
        while True:
            m = ch.read()
            if not m:
                time.sleep(0)
    finally:
        ch.close()
        sys.stdout.write('channel closed...\n')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

