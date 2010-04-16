#!/usr/bin/env python
import sys
import os
import time
import canchannel
import canmsg
import optparse
import udpclient

canOK = 0
canERR_NOMSG = -2

def debug(str):
    sys.stdout.write(str)
    sys.stdout.flush()

EOF = -1
ERROR_PADDING = -2

DLE = 0x10
STX = 0x02
ETX = 0x03

class UDP_DLE(object):
    def __init__(self, port):
        self.port = port
        self.get_start = True
        self.got_dle = False
        self.frame = []

    def dle_pad(self, byte):
        if byte == DLE:
            return (DLE, DLE)
        return (byte,)

    def send(self, frame):
        data = [DLE, STX]
        for b in frame:
            data.append(b)
            if b == DLE:
                data.append(b)
        data = data + [DLE, ETX]
        try:
            d = ''.join([chr(x) for x in data])
        except:
            print 'barf 1'
            print data
            return
        self.port.send(d)

    def read(self, frames):
        try:
            buf = self.port.recv(4096)
        except:
            buf = ''
        for b in buf:
            b = ord(b)
            if self.get_start:
                if self.got_dle:
                    self.got_dle = False
                    if b == STX:
                        self.get_start = False
                        self.frame = []
                else:
                    if b == DLE:
                        self.got_dle = True
            else:
                if self.got_dle:
                    self.got_dle = False
                    if b == ETX:
                        self.get_start = True
                        frames.append(self.frame)
                    elif b == DLE:
                        self.frame.append(b)
                    elif b == STX:
                        self.frame = []
                    else:
                        self.get_start = True
                        sys.stderr.write('DLE: ERROR_PADDING\n')
                elif b == DLE:
                    self.got_dle = True
                else:
                    self.frame.append(b)

class UDPCanChannel(canchannel.CanChannel):
    def __init__(self, ip='localhost', port=2000):
        canchannel.CanChannel.__init__(self)
        self.port = udpclient.UdpClient((ip, port))
        self.dle_handler = UDP_DLE(self.port)
        self.frames = []

    def frame2can(self, frame):
        m = canmsg.CanMsg()
        if frame[0] == 0xFF:
            m.flags = canmsg.canMSG_STD
            m.id = (frame[1] << 8) | frame[2]
            m.data = frame[3:-1]
        elif frame[0] == 0xFE:
            m.flags = canmsg.canMSG_EXT
            m.id = (frame[1] << 24) | (frame[2] << 16) | (frame[3] << 8) | frame[4]
            m.data = frame[5:-1]
        return m

    def do_read(self):
        self.dle_handler.read(self.frames)
        if len(self.frames) > 0:
            m = self.frame2can(self.frames.pop(0))
            m.time = self.gettime() - self.starttime
            return m
        return None

    def do_write(self, msg):
        if msg.flags & canmsg.canMSG_EXT:
            head = [0xFE, (msg.id >> 24) & 0xFF, (msg.id >> 16) & 0xFF, (msg.id >> 8) & 0xFF, msg.id & 0xFF]
        else:
            head = [0xFF, (msg.id >> 8) & 0xFF, msg.id & 0xFF]
        d = head + msg.data
        cs = 0xFF & (0x100 - (sum(d) & 0xFF))
        d.append(cs)
        self.dle_handler.send(d)
        msg.time = self.gettime() - self.starttime

class UDPOptions(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)

def parse_args():
    return UDPOptions().parse_args()

def main(channel):
    canchannel.main(channel)

if __name__ == '__main__':
    try:
        opts, args = parse_args()

        class UCC(UDPCanChannel):
            def message_handler(self, m):
                print m
                return
                if m.sent:
                    try:
                        self.send_cnt += 1
                    except:
                        self.send_cnt = 0
                    print self.send_cnt, m
                else:
                    try:
                        self.rec_cnt += 1
                    except:
                        self.rec_cnt = 0
                    print self.rec_cnt, m

            def action_handler(self, c):
                if c == 'o':
                    m = canmsg.CanMsg()
                    m.id = (canmsg.GROUP_POUT << 27) | (1 << 23) | (1 << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0x01]
                    self.write(m)
                elif c == 's':
                    m = canmsg.CanMsg()
                    m.id = (canmsg.GROUP_PIN << 9) | (1 << 3) | canmsg.TYPE_IN
                    m.flags = canmsg.canMSG_STD
                    m.data = [ord(c) for c in 'hejsan']
                    self.write(m)
                elif c == 'm':
                    m = canmsg.CanMsg()
                    m.id = (canmsg.GROUP_POUT << 27) | (1 << 26) | (2 << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    self.write(m)
                else:
                    try:
                        self.i += 1
                    except:
                        self.i = 0
                    m = canmsg.CanMsg()
                    m.id = (canmsg.GROUP_PIN << 27) | (1 << 3) | canmsg.TYPE_IN
                    m.flags = canmsg.canMSG_EXT
                    m.data = [self.i & 0xFF]
                    self.write(m)

        cc = UCC(ip = args[0], port = int(args[1]))
        main(cc)
    except KeyboardInterrupt:
        pass

def foo():
    pass

