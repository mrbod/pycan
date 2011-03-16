#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

def B50_ID(uid):
    return ((1 << 23) | uid) 

class BICAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        self.run_thread = True
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.id = B50_ID(0)
        self.send_cnt = 0
        self.recv_cnt = 0
        self.send_primary = False
        self.exception = None
        self.run_primary = False
        self.load = False
        self.primary = canmsg.CanMsg()
        self.primary.id = (canmsg.GROUP_PIN << 27) | (self.id << 3) | canmsg.TYPE_IN
        self.primary.flags = canmsg.canMSG_EXT
        self.primary.data = [0x01, 0x00]
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_125K)
        self.thread.start()

    def run(self):
        T0 = time.time()
        try:
            try:
                while self.run_thread:
                    if not self.load:
                        time.sleep(0.001)
                    T = time.time()
                    if T - T0 > 0.4:
                        T0 = T
                        if self.run_primary:
                            self.write(self.primary)
                    elif self.send_primary:
                        self.send_primary = False
                        self.write(self.primary)
                    elif self.load:
                        self.write(self.primary)
            except Exception, e:
                self.exception = e
                raise
        finally:
            sys.stderr.write('send: %d\nrecv: %d\n' % (self.send_cnt, self.recv_cnt))
            sys.stderr.flush()

    def action_handler(self, c):
        if c == 'p':
            self.run_primary = not self.run_primary
        elif c == 'l':
            self.load = not self.load
        elif c == 'P':
            d = self.primary.data[-1]
            d +=1
            self.primary.data[-1] = d & 0xFF
            self.send_primary = True
        elif c in 'cC':
            config = canmsg.CanMsg()
            config.id = (canmsg.GROUP_CFG << 27) | (self.id << 3) | canmsg.TYPE_IN
            config.flags = canmsg.canMSG_EXT
            config.data = [0, 50, 0, 255, 255, 255]
            if c == 'C':
                for i in range(1000):
                    config.data = [0, 50, 0, 0, (i >> 8) & 0xFF, i & 0xFF]
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
        fmt = '%8.3f %s %d:%s\n'
        s = fmt % (m.time, m.stcan(), m.dlc(), m.data_str())
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
    channel = 0
    i = 1
    while i < len(sys.argv):
        o = sys.argv[i]
        if o == '-s':
            silent = True
        if o == '-c':
            try:
                channel = int(sys.argv[i + 1])
                i += 1
            except:
                pass
        i += 1

    c = BICAN(channel, silent=silent)
    try:
        c.open()
        kvaser.main(c)
    finally:
        c.exit_handler()
