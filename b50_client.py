#!/usr/bin/env python
import sys
import os
import time
import canchannel
import canmsg
import optparse
import udpclient
import threading
import dle

canOK = 0
canERR_NOMSG = -2

def debug(str):
    sys.stdout.write(str)
    sys.stdout.flush()

BUID = ((1 << 23) | 0x1)

class UDPPort(object):
    def __init__(self, port=None):
        self.port = udpclient.UdpClient(port)
        self.outbuf = []
        self.inbuf = ''
        self.inbuf_size = 0

    def read(self):
        if self.inbuf_size <= 0:
            try:
                self.inbuf = self.port.recv(4096)
                self.inbuf_size = len(self.inbuf)
            except:
                self.inbuf = ''
                self.inbuf_size = 0
                return dle.EOF
        b = self.inbuf[-self.inbuf_size]
        self.inbuf_size -= 1
        return ord(b)

    def write(self, byte):
        if byte == None:
            d = ''.join([chr(x) for x in self.outbuf])
            self.port.send(d)
            self.outbuf = []
        elif byte > 255:
            import traceback
            traceback.print_stack()
            print 'outbuf: %s' % str(self.outbuf)
            raise Exception('UDPPort.write(%s)' % str(byte))
        else:
            self.outbuf.append(byte)

class UDPCanChannel(canchannel.CanChannel):
    def __init__(self, ip='localhost', port=2000):
        canchannel.CanChannel.__init__(self)
        self.dle_handler = dle.DLEHandler(UDPPort((ip, port)))
        self.outqueue = []
        self.supervised = set()
        self.run_thread = True
        self.thread = threading.Thread(target=self.run)
        self.exception = None
        self.send_idle = False
        self.frames = []
        self.count = 0
        self.thread.start()

    def checksum(self, data):
        s = sum(data) & 0xFF
        if s > 0:
            return 0x100 - s
        return 0x00

    def send_frame(self, frame):
        cs = self.checksum(frame)
        self.dle_handler.send(frame + [cs])

    def idle(self):
        if self.first_idle:
            self.first_idle = False
            d = [0x01, 0, 0, 30*4, 0]
            self.send_frame(d)
            sys.stdout.write('idle set\n')
            sys.stdout.flush()
        elif self.last_idle:
            self.last_idle = False
            self.send_idle = False
            d = [0x01, 0, 0, 0, 0]
            self.send_frame(d)
            sys.stdout.write('idle stop\n')
            sys.stdout.flush()
        else:
            m = canmsg.CanMsg()
            m.count = self.count
            m.id = 0x66
            m.flags = canmsg.canMSG_EXT
            m.data = [0x01]
            self.write(m)

    def run(self):
        sys.stderr.write('thread starting\n')
        sys.stderr.flush()
        T0 = time.time()
        try:
            try:
                while self.run_thread:
                    while len(self.outqueue) > 0:
                        self.write(self.outqueue[0])
                        del(self.outqueue[0])
                    time.sleep(0.01)
                    T = time.time()
                    if T - T0 > 1.0:
                        T0 = T
                        if self.send_idle:
                            self.idle()
            except Exception, e:
                self.exception = e
                raise
        finally:
            sys.stderr.write('thread done\n')
            sys.stderr.flush()

    def exit_handler(self):
        self.run_thread = False
        canchannel.CanChannel.exit_handler(self)

    def frame2can(self, frame):
        m = canmsg.CanMsg()
        if frame[0] == 0xFF:
            m.flags = canmsg.canMSG_STD
            m.count = (frame[1] << 8) | frame[2]
            m.id = (frame[3] << 8) | frame[4]
            m.data = frame[5:-1]
        elif frame[0] == 0xFE:
            m.flags = canmsg.canMSG_EXT
            m.count = (frame[1] << 8) | frame[2]
            m.id = (frame[3] << 24) | (frame[4] << 16) | (frame[5] << 8) | frame[6]
            m.data = frame[7:-1]
        else:
            return None
        return m

    def do_read(self):
        try:
            frame = self.dle_handler.read()
            if isinstance(frame, list):
                m = self.frame2can(frame)
                if m:
                    m.time = self.gettime() - self.starttime
                    return m
            elif not isinstance(frame, int):
                raise Exception('unknown frame type')
            return None

        except Exception, e:
            sys.stderr.write('do_read: %s\n' % str(e))
            sys.stderr.flush()
            raise

    def do_write(self, msg):
        if msg.flags & canmsg.canMSG_EXT:
            head = [0xFE]
            head += [(self.count >> 8) & 0xFF, self.count & 0xFF]
            head += [(msg.id >> 24) & 0xFF, (msg.id >> 16) & 0xFF, (msg.id >> 8) & 0xFF, msg.id & 0xFF]
        else:
            head = [0xFF]
            head += [(self.count >> 8) & 0xFF, self.count & 0xFF]
            head += [(msg.id >> 8) & 0xFF, msg.id & 0xFF]
        d = head + msg.data
        self.send_frame(d)
        msg.time = self.gettime() - self.starttime

class UDPOptions(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        self.add_option(
                '-i', '--buid',
                dest='buid', type='int', default=((1 << 23) | 0x40),
                help='gateway unique id',
                metavar='BUID')

def parse_args():
    return UDPOptions().parse_args()

def main(channel):
    canchannel.main(channel)

if __name__ == '__main__':
    try:
        opts, args = parse_args()
        BUID = opts.buid

        class UCC(UDPCanChannel):
            def dump_msg(self, m):
                if m.sent:
                    try:
                        self.count += 1
                    except:
                        self.count = 0
                    m.count = self.count
                fmt = '%05d %8.3f %08X %08X %d:%s\n'
                s = fmt % (m.count, m.time, m.id, m.addr(), m.dlc(), m.data_str())
                if m.sent:
                    sys.stdout.write('W ' + s)
                else:
                    sys.stdout.write('R ' + s) 

            def message_handler(self, m):
                self.dump_msg(m)
                buid = m.addr()
                if not m.sent:
                    if buid == BUID:
                        if (m.group() == canmsg.GROUP_SEC) and (m.data[1] == 41):
                            id = (m.data[2] << 24) | (m.data[3] << 16) | (m.data[4] << 8) | m.data[5]
                            self.supervised.discard(id)
                    else:
                        if m.id not in self.supervised:
                            self.supervised.add(m.id)
                            msg = canmsg.CanMsg()
                            msg.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                            msg.flags = canmsg.canMSG_EXT
                            msg.data = [0x00, 84, (m.id >> 24) & 0xFF, (m.id >> 16) & 0xFF, (m.id >> 8) & 0xFF, m.id & 0xFF, 3, 0]
                            self.outqueue.append(msg)
                if self.exception:
                    raise self.exception

            def action_handler(self, c):
                if c in 'Ii':
                    if c == 'i':
                        self.first_idle = True
                        self.last_idle = False
                        self.send_idle = True
                    else:
                        self.last_idle = True
                    return
                m = canmsg.CanMsg()
                m.count = self.count
                if c == 'o':
                    m.id = (canmsg.GROUP_POUT << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0x01]
                    self.write(m)
                elif c == 'O':
                    m.id = (canmsg.GROUP_POUT << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0x00]
                    self.write(m)
                elif c == 'r':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 86, 0, 1]
                    self.write(m)
                elif c in 'u':
                    m.id = (canmsg.GROUP_SEC << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0x00, 40, 0x0C, 0x00, 0x00, 0x01]
                    self.write(m)
                elif c in 'mM1!2"3#':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    if c == 'm':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x01, 3, 0]
                    elif c == 'M':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x01, 0, 0]
                    elif c == '1':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x49, 3, 0]
                    elif c == '!':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x49, 0, 0]
                    elif c == '2':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x51, 3, 0]
                    elif c == '"':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x51, 0, 0]
                    elif c == '3':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x59, 3, 0]
                    elif c == '#':
                        m.data = [0x00, 84, 0x0C, 0x00, 0x00, 0x59, 0, 0]
                    self.write(m)
                elif c in 'rR':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    if c == 'r':
                        m.data = [0x00, 85, 0, 0, 0, 7, 1, 0]
                    else:
                        m.data = [0x00, 85, 0, 0, 0, 7, 0, 0]
                    self.write(m)
                elif c == 'v':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 99, 0, 30]
                    self.write(m)
                elif c == 'V':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 99, 0, 31]
                    self.write(m)
                elif c == 's':
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 99, 0, 92]
                    self.write(m)
                elif c == 't':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 87, 0, 0, 0x05, 0xDC]
                    self.write(m)
                elif c == 'a':
                    m.id = (canmsg.GROUP_CFG << 27) | (BUID << 3) | canmsg.TYPE_OUT
                    m.flags = canmsg.canMSG_EXT
                    m.data = [0, 99, 0, 93]
                    self.write(m)
                else:
                    try:
                        self.i += 1
                    except:
                        self.i = 0
                    m.id = 7
                    m.flags = canmsg.canMSG_EXT
                    m.data = [self.i & 0xFF]
                    self.write(m)

        cc = UCC(ip = args[0], port = int(args[1]))
        try:
            main(cc)
        finally:
            cc.exit_handler()
    except KeyboardInterrupt:
        pass

