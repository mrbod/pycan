#!/bin/env python
import stcan
import sys
import time
import threading
import socketcan
import random

def B50_ID(uid):
    return ((0 << 23) | uid) 

def myid(x):
    return (stcan.GROUP_PIN << 27) | (B50_ID(x) << 3) | stcan.TYPE_IN

class BICAN(socketcan.SocketCanChannel):
    def __init__(self, channel=0, silent=False, nodes=10):
        self.nodes = [self.gen_msg(myid(x + 1)) for x in range(nodes)]
        self.node_count = len(self.nodes)
        self.max_addr = B50_ID(self.node_count)
        self.run_thread = True
        self.thread = threading.Thread(target=self.run, name='Worker')
        self.exception = None
        socketcan.SocketCanChannel.__init__(self, silent=silent, channel=channel)
        self.thread.start()

    def gen_msg(self, id, t=0.0):
        m = stcan.StCanMsg(id=id, time=t, extended=True, data=[0, 0])
        return m

    def run(self):
        try:
            while self.run_thread:
                time.sleep(0.010)
                self.nodes[random.randint(0, self.node_count-1)].data[0] ^= 1
                for i in xrange(self.node_count):
                    m = self.nodes[i]
                    T = time.time()
                    if (T - m.time) > 0.4:
                        self.write(m)
                        self.nodes[i] = self.gen_msg(m.id, T)
        except Exception, e:
            self.exception = e
            raise

    def handle_config(self, m):
        index = m.get_word(0)
        if index == 99:
            ask = m.get_word(1)
            if ask == 30:
                # node type
                i = (stcan.GROUP_CFG << 27) | (m.addr << 3) | stcan.TYPE_IN
                d = [0x00, 0x1E, 0x90, 0x00]
                msg = stcan.StCanMsg(id=i, data=d, extended=m.extended)
                self.write(msg)
            elif ask == 31:
                # sw version
                i = (stcan.GROUP_CFG << 27) | (m.addr << 3) | stcan.TYPE_IN
                d = [0x00, 0x1F, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00]
                msg = stcan.StCanMsg(id=i, data=d, extended=m.extended)
                self.write(msg)

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if not m.sent:
            if m.addr <= self.max_addr:
                if m.type == stcan.TYPE_OUT:
                    if m.group == stcan.GROUP_CFG:
                        self.handle_config(m)

    def exit_handler(self):
        self.run_thread = False

class Log(object):
    def log(self, txt):
        print txt

    def info(self, row, txt):
        self.log(txt)

def main(ch):
    T0 = time.time()
    while True:
        T = time.time()
        m = ch.read()
        if m:
            #print m
            pass
        elif T - T0 > 10.0:
            T0 = T
            sys.stderr.write('Read: {0.read_cnt}, Write: {0.write_cnt}\n'.format(ch))
        else:
            time.sleep(0.010)

if __name__ == '__main__':
    channel = 0
    nodecnt = 5
    i = 1
    while i < len(sys.argv):
        o = sys.argv[i]
        if o == '-c':
            try:
                nodecnt = int(sys.argv[i + 1])
                i += 1
            except:
                pass
        i += 1

    logger = Log()
    c = BICAN(channel, nodes=nodecnt)
    c.logger = logger
    try:
        main(c)
    except KeyboardInterrupt:
        pass
    finally:
        c.exit_handler()

