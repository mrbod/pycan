#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser
import random

def B50_ID(uid):
    return ((1 << 23) | uid) 

def myid(x):
    return (canmsg.GROUP_PIN << 27) | (B50_ID(x) << 3) | canmsg.TYPE_IN

class BICAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False):
        F = canmsg.canMSG_EXT
        self.nodes = [canmsg.CanMsg(id=myid(x + 1), flags=F, data=[0, 0]) for x in range(55)]
        self.node_count = len(self.nodes)
        self.max_addr = B50_ID(self.node_count)
        self.run_thread = True
        self.thread = threading.Thread(target=self.run, name='Worker')
        self.activated = None
        self._activate = True
        self.send_cnt = 0
        self.send_tot = 0
        self.recv_cnt = 0
        self.recv_tot = 0
        self.send_primary = False
        self.exception = None
        self.run_primary = False
        self.load = False
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=kvaser.canBITRATE_125K)
        self.log_time = self.gettime()
        self.thread.start()

    def activate(self):
        if self._activate:
            self._activate = False
            self.activated = random.choice(self.nodes)
            self.activated.data[0] = 1
            self.write(self.activated)
        else:
            self._activate = True
            self.activated.data[0] = 0
            self.write(self.activated)

    def run(self):
        T0 = self.gettime()
        loggT = T0
        try:
            try:
                while self.run_thread:
                    T = self.gettime()
                    if (T - T0) > 0.01:
                        self.activate()
                        T0 = T
                    dt = T - loggT
                    if dt > 1.0:
                        loggT = T
                        sfps = self.send_cnt / dt
                        self.send_cnt = 0
                        self.log('{0:.3f}'.format(sfps))
                        rfps = self.recv_cnt / dt
                        self.recv_cnt = 0
                    for m in self.nodes:
                        if (T - m.time) > 0.4:
                            self.write(m)
            except Exception, e:
                self.exception = e
                raise
        finally:
            sys.stderr.write('send: %d\nrecv: %d\n' % (self.send_tot, self.recv_tot))
            sys.stderr.flush()

    def action_handler(self, c):
        if c in 'pP':
            self.run_primary = not self.run_primary

    def handle_config(self, m):
        index = m.get_word(0)
        if index == 99:
            ask = m.get_word(1)
            if ask == 30:
                # node type
                i = (canmsg.GROUP_CFG << 27) | (m.addr() << 3) | canmsg.TYPE_IN
                d = [0x00, 0x1E, 0x90, 0x00]
                msg = canmsg.CanMsg(id = i, data = d, flags = m.flags)
                self.write(msg)
            elif ask == 31:
                # sw version
                i = (canmsg.GROUP_CFG << 27) | (m.addr() << 3) | canmsg.TYPE_IN
                d = [0x00, 0x1F, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00]
                msg = canmsg.CanMsg(id = i, data = d, flags = m.flags)
                self.write(msg)

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if m.sent:
            self.send_cnt += 1
            self.send_tot += 1
        else:
            self.recv_cnt += 1
            self.recv_tot += 1
            if m.extended() and (m.addr() <= self.max_addr):
                if m.type() == canmsg.TYPE_OUT:
                    if m.group() == canmsg.GROUP_CFG:
                        self.handle_config(m)

    def exit_handler(self):
        self.run_thread = False

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
