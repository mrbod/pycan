#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser
import random

def B50_ID(uid):
    return ((0 << 23) | uid) 

def myid(x):
    return (canmsg.GROUP_PIN << 27) | (B50_ID(x) << 3) | canmsg.TYPE_IN

class BICAN(kvaser.KvaserCanChannel):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            sys.stderr.write('%s = %s\n' % (k, v))
        nodes = kwargs.pop('nodes', None)
        if nodes == None:
            nodes = 10
        self.nodes = [self.gen_msg(myid(x + 1)) for x in range(nodes)]
        self.node_count = len(self.nodes)
        self.max_addr = B50_ID(self.node_count)
        self.run_thread = True
        self.thread = threading.Thread(target=self.run, name='Worker')
        self.exception = None
        self.start_time = time.time()
        super(BICAN, self).__init__(*args, **kwargs)
        self.thread.start()

    def gen_msg(self, id):
        m = canmsg.CanMsg(id=id, extended=True, data=[0, 0])
        return m

    def gettime(self):
        return time.time() - self.start_time

    def run(self):
        try:
            for m in self.nodes:
                self.write(m)
            eventT = time.time()
            eventN = None
            event_interval = 1.0
            while self.run_thread:
                time.sleep(0.010)
                T = time.time()
                if T - eventT > event_interval:
                    eventT = T
                    if eventN == None:
                        eventN = random.randint(0, self.node_count-1)
                        m = self.nodes[eventN]
                        m.data[0] ^= 1
                        event_interval = 0.3
                    else:
                        m = self.nodes[eventN]
                        m.data[0] ^= 1
                        eventN = None
                        event_interval = 1.0
                    self.write(m)
                for i, m in enumerate(self.nodes):
                    T = self.gettime()
                    if (T - m.time) > 0.4:
                        self.write(m)
                    self.nodes[i] = canmsg.CanMsg(data=m)
        except Exception, e:
            self.exception = e
            raise

    def handle_config(self, m):
        index = m.get_word(0)
        if index == 99:
            ask = m.get_word(1)
            if ask == 30:
                # node type
                i = (canmsg.GROUP_CFG << 27) | (m.addr << 3) | canmsg.TYPE_IN
                d = [0x00, 0x1E, 0x90, 0x00]
                msg = canmsg.CanMsg(id=i, data=d, extended=m.extended)
                self.write(msg)
            elif ask == 31:
                # sw version
                i = (canmsg.GROUP_CFG << 27) | (m.addr << 3) | canmsg.TYPE_IN
                d = [0x00, 0x1F, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00]
                msg = canmsg.CanMsg(id=i, data=d, extended=m.extended)
                self.write(msg)

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if not m.sent:
            if m.addr <= self.max_addr:
                if m.type == canmsg.TYPE_OUT:
                    if m.group == canmsg.GROUP_CFG:
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
    try: 
        nodecnt = int(sys.argv[1])
    except:
        sys.stderr.write('usage: %s <node count> [channel]\n' % sys.argv[0])
        sys.exit(1)
    try: 
        channel = int(sys.argv[2])
        sys.stdout.write('using channel: %d\n' % channel)
    except:
        channel = 0
        sys.stdout.write('using default channel: 0\n')
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
    c = BICAN(channel=channel, nodes=nodecnt)
    c.logger = logger
    try:
        main(c)
    except KeyboardInterrupt:
        pass
    finally:
        c.exit_handler()

