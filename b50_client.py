#!/usr/bin/env python
import sys
import os
import time
import canchannel
import stcan
import optparse
import udpclient
import threading
import random
import dle

canOK = 0
canERR_NOMSG = -2

BUID = ((1 << 23) | 0x1)

def buid2id(buid):
    return buid << 3

def id2buid(id):
    return (id >> 3) & 0x00FFFFFF

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

class App(object):
    def __init__(self, channel):
        self.channel = channel
        self.cnt = 0
        self.thread = threading.Thread(target=self.run)
        self._run = True
        self._lock = threading.Lock()
        self._nodes = {}
        self._xnodes = self._nodes.values()
        self.thread.start()

    def stop(self):
        self._run = False

    def add(self, node):
        self._lock.acquire()
        try:
            self._nodes[node.addr] = node
            self._xnodes = self._nodes.values()
            self.cnt = len(self._xnodes)
        finally:
            self._lock.release()

    def remove(self, buid):
        self._lock.acquire()
        try:
            try:
                del self._nodes[buid]
                self._xnodes = self._nodes.values()
                self.cnt = len(self._xnodes)
            except:
                pass
        finally:
            self._lock.release()
        
    def run(self):
        while self._run:
            time.sleep(0.5)
            self._lock.acquire()
            cnt = self.cnt
            if cnt > 20:
                cnt = 20
            try:
                try:
                    for i in range(cnt):
                        node = random.choice(self._xnodes)
                        if node.data[0] == 0:
                            node.data[0] = 1
                        else:
                            node.data[0] = 0
                        self.channel.write(node)
                except:
                    pass
            finally:
                self._lock.release()

class UDPCanChannel(canchannel.CanChannel):
    def __init__(self, ip='localhost', port=2000):
        self.app = App(self)
        canchannel.CanChannel.__init__(self)
        self.dle_handler = dle.DLEHandler(UDPPort((ip, port)))
        self.outqueue = []
        self.managed = set()
        self.version_asked = set()
        self.version_received = set()
        self.type_asked = set()
        self.type_received = set()
        self.run_thread = True
        self.thread = threading.Thread(target=self.run)
        self.exception = None
        self.first_idle = True
        self.last_idle = False
        self.send_idle = True
        self.frames = []
        self.count_out = 0
        self.count_in = 0
        self.errcnt = 0
        self.gw_open = True
        self.thread.start()

    @property
    def nodecnt(self):
        return self.app.cnt

    def checksum(self, data):
        s = sum(data) & 0xFF
        if s > 0:
            return 0x100 - s
        return 0x00

    def send_frame(self, frame_type, frame):
        head = [frame_type
                , (self.count_out >> 8) & 0xFF
                , self.count_out & 0xFF]
        frame = head + frame
        cs = self.checksum(frame)
        self.dle_handler.send(frame + [cs])
        #self.errcnt += 1
        #if self.errcnt >= 10:
            #self.errcnt = 0
            #self.count_out += 1
            #self.info(2, 'error induced')
        self.count_out = (self.count_out + 1) & 0xFFFF


    def idle(self):
        if self.first_idle:
            self.first_idle = False
            d = [0, 0, 30*4, 0]
            self.send_frame(0x01, d)
        elif self.last_idle:
            self.last_idle = False
            self.send_idle = False
            d = [0, 0, 0, 0]
            self.send_frame(0x01, d)
        else:
            m = stcan.StCanMsg(extended = True)
            m.id = (stcan.GROUP_POUT << 27) | (BUID << 3) | stcan.TYPE_OUT
            if self.gw_open:
                m.data = [0x01]
            else:
                m.data = [0x00]
            self.write(m)

    def run(self):
        T0 = self.gettime()
        try:
            nodecnt = self.nodecnt
            while self.run_thread:
                if nodecnt != self.nodecnt:
                    nodecnt = self.nodecnt
                    self.info(2, 'Serving {0} nodes    '.format(nodecnt))
                while len(self.outqueue) > 0:
                    self.write(self.outqueue[0])
                    del(self.outqueue[0])
                time.sleep(0.01)
                T = self.gettime()
                if T - T0 > 1.0:
                    T0 = T
                    if self.send_idle:
                        self.idle()
        except Exception, e:
            self.exception = e
            raise

    def exit_handler(self):
        self.app.stop()
        self.run_thread = False
        canchannel.CanChannel.exit_handler(self)

    def frame2can(self, frame):
        count = (frame[1] << 8) | frame[2]
        if count != self.count_in:
            f = [0, 0x01, # dle err type
                 (self.count_in >> 8) &  0xff,
                 self.count_in & 0xff,
                 (count >> 8) &  0xff,
                 count & 0xff]
            self.send_frame(0x02, f)
            s =  'DROPPED FRAME: got {0}, expected {1}'
            self.info(4, s.format(count, self.count_in))
        self.count_in = (count + 1) & 0xFFFF
        if frame[0] == 0xFF:
            E = False
            ID = (frame[3] << 8) | frame[4]
            D = frame[5:-1]
            return stcan.StCanMsg(id=ID, extended=E, data=D)
        elif frame[0] == 0xFE:
            E = True
            ID = (frame[3] << 24) | (frame[4] << 16) | (frame[5] << 8) | frame[6]
            D = frame[7:-1]
            return stcan.StCanMsg(id=ID, extended=E, data=D)
        elif frame[0] == 0x02:
            err_type = (frame[3] << 8) | frame[4]
            if err_type == 1:
                exp = (frame[5] << 8) | frame[6]
                rec = (frame[7] << 8) | frame[8]
                s = 'GW DROPPED FRAMES: expected {0}, got {1}'
                self.info(5, s.format(exp, rec))
            else:
                self.info(5, 'Unknown dle error: {0}'.format(err_type))
        return None

    def do_read(self):
        try:
            frame = self.dle_handler.read()
            if isinstance(frame, list):
                m = self.frame2can(frame)
                if m:
                    m.time = self.gettime()
                    return m
            elif not isinstance(frame, int):
                raise Exception('unknown frame type')
            return None

        except Exception, e:
            self.info(5, 'do_read: %s' % str(e))
            raise

    def do_write(self, msg):
        if msg.extended:
            frame_type = 0xFE
            head = [(msg.id >> 24) & 0xFF, (msg.id >> 16) & 0xFF, (msg.id >> 8) & 0xFF, msg.id & 0xFF]
        else:
            frame_type = 0xFF
            head = [(msg.id >> 8) & 0xFF, msg.id & 0xFF]
        d = head + msg.data
        self.send_frame(frame_type, d)
        msg.time = self.gettime()

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
    import interface
    i = interface.Interface(channel)
    i.run()

if __name__ == '__main__':
    import logrot
    logger = logrot.logger('b50_client.log')

    try:
        opts, args = parse_args()
        BUID = opts.buid

        class UCC(UDPCanChannel):
            def ask_type(self, buid):
                self.type_asked.add(buid)
                i = (stcan.GROUP_CFG << 27) | (buid << 3) | stcan.TYPE_OUT
                msg = stcan.StCanMsg(id = i, extended = True)
                msg.data = [0, 0x63, 0, 0x1E]
                self.outqueue.append(msg)

            def ask_version(self, buid):
                self.version_asked.add(buid)
                i = (stcan.GROUP_CFG << 27) | (buid << 3) | stcan.TYPE_OUT
                msg = stcan.StCanMsg(id = i, extended = True)
                msg.data = [0, 0x63, 0, 0x1F]
                self.outqueue.append(msg)

            def manage(self, id):
                self.managed.add(id)
                i = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                msg = stcan.StCanMsg(id = i, extended = True)
                msg.data = [0x00, 84,
                            (id >> 24) & 0xFF, (id >> 16) & 0xFF,
                            (id >> 8) & 0xFF, id & 0xFF,
                            0x02, 0x58]
                self.outqueue.append(msg)

            def add_app(self, buid):
                i = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                msg = stcan.StCanMsg(id = i, extended = True)
                id = (stcan.GROUP_POUT << 27) | (buid << 3) | stcan.TYPE_OUT
                msg.data = [0x00, 85,
                            (id >> 24) & 0xFF, (id >> 16) & 0xFF,
                            (id >> 8) & 0xFF, id & 0xFF,
                            0x01, 0x90]
                self.outqueue.append(msg)
                msg = stcan.StCanMsg(id = id, extended = True)
                msg.data = [0x00, 0x00]
                self.app.add(msg)

            def message_handler(self, m):
                self.log(m)
                logger.debug(str(m))
                if m.sent:
                    pass
                else:
                    buid = m.addr
                    g = m.group
                    if buid == BUID:
                        if (g == stcan.GROUP_SEC) and (m.data[1] == 41):
                            id = (m.data[2] << 24) | (m.data[3] << 16) | (m.data[4] << 8) | m.data[5]
                            self.managed.discard(id)
                            addr = id2buid(id)
                            self.version_received.discard(addr)
                            self.type_received.discard(addr)
                            self.app.remove(addr)
                            self.info(3, 'GW dropped CAN id {0:08X}'.format(id))
                    else:
                        if m.id in self.managed:
                            pass
                        else:
                            if g == stcan.GROUP_PIN:
                                if buid not in self.type_received:
                                    if buid not in self.type_asked:
                                        self.ask_type(buid)
                                elif buid not in self.version_received:
                                    if buid not in self.version_asked:
                                        self.ask_version(buid)
                                else:
                                    self.version_asked.discard(buid)
                                    self.type_asked.discard(buid)
                                    self.manage(m.id)
                                    self.add_app(buid)
                            elif g == stcan.GROUP_CFG:
                                cmd = m.get_word(0)
                                if cmd == 0x1E:
                                    self.type_received.add(buid)
                                elif cmd == 0x1F:
                                    self.version_received.add(buid)
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
                if c == 'o':
                    self.gw_open = not self.gw_open
                    return
                m = stcan.StCanMsg(extended = True)
                if c == 'r':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0, 86, 0, 1]
                elif c in 'u':
                    m.id = (stcan.GROUP_SEC << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0x00, 40, 0x0C, 0x00, 0x00, 0x01]
                elif c in 'mM1!2"3#':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
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
                elif c in 'rR':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    if c == 'r':
                        m.data = [0x00, 85, 0, 0, 0, 7, 1, 0]
                    else:
                        m.data = [0x00, 85, 0, 0, 0, 7, 0, 0]
                elif c == 'v':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0, 99, 0, 30]
                elif c == 'V':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0, 99, 0, 31]
                elif c == 's':
                    m.data = [0, 99, 0, 92]
                elif c == 't':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0, 87, 0, 0, 0x05, 0xDC]
                elif c == 'a':
                    m.id = (stcan.GROUP_CFG << 27) | (BUID << 3) | stcan.TYPE_OUT
                    m.data = [0, 99, 0, 93]
                else:
                    try:
                        self.i += 1
                    except:
                        self.i = 0
                    m.id = 7
                    m.data = [self.i & 0xFF]
                self.write(m)

        cc = UCC(ip = args[0], port = int(args[1]))
        try:
            main(cc)
        finally:
            cc.exit_handler()
    except KeyboardInterrupt:
        pass

