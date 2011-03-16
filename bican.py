#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

class BICAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.send_cnt = 0
        self.recv_cnt = 0
        self.send_primary = False
        self.exception = None
        self.primary = canmsg.CanMsg()
        self.primary.id = (canmsg.GROUP_POUT << 27) | (((1 << 23) | 5) << 3) | canmsg.TYPE_OUT
        self.primary.flags = canmsg.canMSG_EXT
        self.primary.data = [0x01, 0x00]
        self.config = canmsg.CanMsg()
        self.config.id = (canmsg.GROUP_CFG << 27) | (((1 << 23) | 5) << 3) | canmsg.TYPE_OUT
        self.config.flags = canmsg.canMSG_EXT
        self.config.data = [0, 50, 0, 255, 255, 255]
        self.thread.start()
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_125K)

    def run(self):
        T0 = time.time()
        try:
            try:
                while self.run_thread:
                    time.sleep(0.01)
                    T = time.time()
                    if T - T0 > 0.4:
                        self.send_primary = True
                    if self.send_primary:
                        T0 = T
                        self.send_primary = False
                        self.write(self.primary)
            except Exception, e:
                self.exception = e
                raise
        finally:
            sys.stderr.write('send: %d\nrecv: %d\n' % (self.send_cnt, self.recv_cnt))
            sys.stderr.flush()

    def action_handler(self, c):
        self.write(self.config)

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
    c = BICAN(1, silent=silent)
    try:
        c.open()
        kvaser.main(c)
    finally:
        c.exit_handler()
