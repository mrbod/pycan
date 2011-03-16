#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

class SE05(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        self.old_recv = canmsg.CanMsg()
        self.old_cnt = 0
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.exception = None
        self.load_msg = canmsg.CanMsg(id=1)
        self.load = False
        self.load_cnt = 0
        self.thread.start()
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_125K)

    def run(self):
        try:
            while self.run_thread:
                if self.load:
                    d = [(self.load_cnt >> 8) & 0xFF, self.load_cnt & 0xFF]
                    self.load_msg.data = d
                    self.write(self.load_msg)
                    self.load_cnt += 1
                    time.sleep(0.001)
        except Exception, e:
            self.exception = e
            raise

    def action_handler(self, c):
        self.load = not self.load

    def message_handler(self, m):
        print m

    def exit_handler(self):
        self.run_thread = False

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

if __name__ == '__main__':
    silent = False
    for o in sys.argv[1:]:
        if o == '-s':
            silent = True
    c = SE05(0, silent=silent)
    try:
        c.open()
        kvaser.main(c)
    finally:
        c.exit_handler()
