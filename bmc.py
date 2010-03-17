#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

class BMCCAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        self.old_recv = canmsg.CanMsg()
        self.old_cnt = 0
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.sendpos = False
        self.exception = None
        id = 0x04 + (1 << 3)
        self.pos = canmsg.CanMsg(id=id, data=[0,7,0,0,0,0])
        self.thread.start()
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_500K)

    def run(self):
        try:
            while self.run_thread:
                if self.sendpos:
                    self.sendpos = False
                    self.write(self.pos)
        except Exception, e:
            self.exception = e
            raise

    def action_handler(self, c):
        pass

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if m == self.old_recv:
            self.old_cnt += 1
        else:
            if self.old_cnt > 0:
                sys.stdout.write('repeated {0:d} times\n'.format(self.old_cnt))
            self.old_recv = m
            self.old_cnt = 0
            self.dump_msg(m)
        if m.id == 0x01:
            self.sendpos = True
        elif m.id == 0x0D:
            self.pos.data = m.data[:]

    def exit_handler(self):
        self.run_thread = False

    def dump_msg(self, m):
        fmt = '{0:8.3f} {1:03X} {2:d}:{3:s}\n'
        s = fmt.format(m.time, m.id, m.dlc(), m.data_str())
        sys.stdout.write(s)

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

if __name__ == '__main__':
    silent = False
    for o in sys.argv[1:]:
        if o == '-s':
            silent = True
    c = BMCCAN(2, silent=silent)
    try:
        c.open()
        kvaser.main(c)
    finally:
        c.exit_handler()
