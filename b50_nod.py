#!/bin/env python
import stcan
import sys
import time
import threading
import socketcan

def B50_ID(uid):
    return ((1 << 23) | uid) 

class BICAN(socketcan.SocketCanChannel):
    def __init__(self, channel=0, silent=False):
        self.run_thread = True
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.can_id = B50_ID(0x2200)
        self.send_primary = False
        self.exception = None
        self.run_primary = False
        self.load = False
        socketcan.SocketCanChannel.__init__(self, channel=channel)
        self.thread.start()

    def gen_primary(self):
        primary = stcan.StCanMsg(extended=True)
        primary.can_id = (stcan.GROUP_PIN << 27) | (self.can_id << 3) | stcan.TYPE_IN
        primary.data = [0x01, 0x00]
        return primary

    def run(self):
        T0 = time.time()
        try:
            while self.run_thread:
                if not self.load:
                    time.sleep(0.001)
                T = time.time()
                if T - T0 > 0.4:
                    T0 = T
                    if self.run_primary:
                        self.write(self.gen_primary())
                elif self.send_primary:
                    self.send_primary = False
                    self.write(self.gen_primary())
                elif self.load:
                    self.write(self.gen_primary())
        except Exception, e:
            self.exception = e
            raise

    def action_handler(self, c):
        if c == 'p':
            self.run_primary = not self.run_primary
        elif c == 'l':
            self.load = not self.load
        elif c == 'P':
            self.send_primary = True
        elif c in 'cC':
            config = stcan.StCanMsg(extended=True)
            config.can_id = (stcan.GROUP_CFG << 27) | (self.can_id << 3) | stcan.TYPE_IN
            config.data = [0, 50, 0, 255, 255, 255]
            if c == 'C':
                for i in range(1000):
                    config.data = [0, 50, 0, 0, (i >> 8) & 0xFF, i & 0xFF]
                    self.write(config)
            else:
                self.write(config)

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
            if m.extended and (m.addr() <= self.can_id):
                if m.type() == stcan.TYPE_OUT:
                    if m.group() == stcan.GROUP_CFG:
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
        import interface
        i = interface.Interface(c)
        i.run()
    finally:
        c.exit_handler()
