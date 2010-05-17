#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

B50_ID = ((1 << 23) | 5) 

class BICAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        self.run_thread = True
        self.thread = threading.Thread(target=self.run)
        self.send_cnt = 0
        self.recv_cnt = 0
        self.send_primary = False
        self.exception = None
        self.send_primary = False
        self.primary = canmsg.CanMsg()
        self.primary.id = (canmsg.GROUP_PIN << 27) | (B50_ID << 3) | canmsg.TYPE_IN
        self.primary.flags = canmsg.canMSG_EXT
        self.primary.data = [0x01, 0x00]
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_125K)
        self.thread.start()

    def run(self):
        T0 = time.time()
        try:
            try:
                while self.run_thread:
                    time.sleep(0.01)
                    T = time.time()
                    if T - T0 > 0.4:
                        T0 = T
                        if self.send_primary:
                            self.write(self.primary)
            except Exception, e:
                self.exception = e
                raise
        finally:
            sys.stderr.write('send: %d\nrecv: %d\n' % (self.send_cnt, self.recv_cnt))
            sys.stderr.flush()

    def action_handler(self, c):
        if c == 'p':
            self.send_primary = not self.send_primary
        elif c in 'cC':
            config = canmsg.CanMsg()
            config.id = (canmsg.GROUP_CFG << 27) | (B50_ID << 3) | canmsg.TYPE_IN
            config.flags = canmsg.canMSG_EXT
            config.data = [0, 50, 0, 255, 255, 255]
            if c == 'C':
                for i in range(1000):
                    self.write(config)
            else:
                self.write(config)

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        self.dump_msg(m)

    def exit_handler(self):
        self.run_thread = False

    def dump_msg(self, m):
        fmt = '%8.3f %08X %d:%s\n'
        s = fmt % (m.time, m.id, m.dlc(), m.data_str())
        if m.sent:
            self.send_cnt += 1
            sys.stdout.write('W ' + s)
        else:
            self.recv_cnt += 1
            sys.stdout.write('R ' + s)

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

if __name__ == '__main__':
    silent = False
    for o in sys.argv[1:]:
        if o == '-s':
            silent = True
    c = BICAN(0, silent=silent)
    try:
        c.open()
        kvaser.main(c)
    finally:
        c.exit_handler()
