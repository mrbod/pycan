#!/bin/env python
import stcan
import sys
import time
import threading
import socketcan
import random

def B50_ID(uid):
    return ((1 << 23) | uid) 

def myid(x):
    return (stcan.GROUP_PIN << 27) | (B50_ID(x) << 3) | stcan.TYPE_IN

class BICAN(socketcan.SocketCanChannel):
    def __init__(self, channel=0, silent=False, nodes=10):
        self.nodes = [self.gen_msg(myid(x + 1)) for x in range(nodes)]
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
        socketcan.SocketCanChannel.__init__(self, silent=silent, channel=channel, msg_class=stcan.StCanMsg)
        self.log_time = self.gettime()
        self.thread.start()

    def gen_msg(self, id):
        m = stcan.StCanMsg(id=id, extended=True, data=[0, 0])
        m.time = time.time()
        return m

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
        try:
            while self.run_thread:
                time.sleep(0.01)
                T = time.time()
                for i in xrange(self.node_count):
                    m = self.nodes[i]
                    if (T - m.time) > 0.4:
                        self.write(m)
                        self.nodes[i] = self.gen_msg(m.id)
                        break
        except Exception, e:
            self.exception = e
            raise

    def action_handler(self, c):
        if c in 'pP':
            self.run_primary = not self.run_primary

    def handle_config(self, m):
        index = m.get_word(0)
        if index == 99:
            ask = m.get_word(1)
            if ask == 30:
                # node type
                i = (stcan.GROUP_CFG << 27) | (m.addr() << 3) | stcan.TYPE_IN
                d = [0x00, 0x1E, 0x90, 0x00]
                msg = stcan.StCanMsg(id = i, data = d, extended = m.extended)
                self.write(msg)
            elif ask == 31:
                # sw version
                i = (stcan.GROUP_CFG << 27) | (m.addr() << 3) | stcan.TYPE_IN
                d = [0x00, 0x1F, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00]
                msg = stcan.StCanMsg(id = i, data = d, extended = m.extended)
                self.write(msg)

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        self.log(m)
        if not m.sent:
            if m.extended and (m.addr() <= self.max_addr):
                if m.type() == stcan.TYPE_OUT:
                    if m.group() == stcan.GROUP_CFG:
                        self.handle_config(m)

    def exit_handler(self):
        self.run_thread = False

def main(ch):
    while True:
        m = ch.read()
        if m:
            print m
        else:
            time.sleep(0.010)

if __name__ == '__main__':
    silent = False
    channel = 0
    nodecnt = 5
    i = 1
    while i < len(sys.argv):
        o = sys.argv[i]
        if o == '-s':
            silent = True
        if o == '-c':
            try:
                nodecnt = int(sys.argv[i + 1])
                i += 1
            except:
                pass
        i += 1

    c = BICAN(channel, silent=silent, nodes=nodecnt)
    try:
        import interface
        i = interface.Interface(c)
        i.run()
    finally:
        c.exit_handler()
