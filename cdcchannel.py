#!/usr/bin/env python
import sys
import re
import socket
import datetime
import threading
import getopt
import Queue
import canchannel
import canmsg

canmsg.format_set(canmsg.FORMAT_STCAN)

_canre = re.compile(r'CAN\s+(?P<channel>\d+)\s+'
                 + r'(?P<id>\w+)\s+'
                 + r'(?P<flags>\w+)\s+'
                 + r'(?P<time>\d+)'
                 + r'(?:\s+(?P<data>\S*))?')

_mfmt = '{0.logtime:s} {0.channel:2d} {0.sid:>8} {0.stcan:^15s} {0.time:10d} {0.data:s}'

class CDCMsg(canmsg.CanMsg):
    def __init__(self, **kwargs):
        super(CDCMsg, self).__init__(**kwargs)
        self.cortex_time = 0
        self.cortex_num = 0
        self.cortex_channel = 0

    def __str__(self):
        s = '{0.cortex_channel:d} {0.cortex_num:3d} '.format(self)
        return s + super(CDCMsg, self).__str__()


class CDCChannel(canchannel.CanChannel):
    def __init__(self, channel=-1, hostname='localhost', port=5555, msg_class=CDCMsg):
        self.channel = channel
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((hostname, port))
        if channel < 0:
            self.socket.send('LOG {0:d}\n'.format(-self.channel))
        else:
            self.socket.send('OPEN {0:d}\n'.format(self.channel))
        self.q = Queue.Queue()
        super(CDCChannel, self).__init__(msg_class=msg_class)
        self.last_msg = {}
        self.drop_cnt = {}

    def read_socket(self):
        self.data = ''
        d = self.socket.recv(4096)
        self.data = self.data + d
        L = self.data.split('\n')
        self.data = L[-1]
        for m in (x for x in (self.cdc_decode(l) for l in L[:-1]) if x):
            self.q.put(m)

    def close(self):
        self.running = False
        self.socket.close()
        super(CDCChannel, self).close()

    def cdc_decode(self, s):
        o = _canre.match(s)
        if o:
            md = o.groupdict()
            sid = md['id']
            C = int(md['channel'])
            ID = int(sid, 16)
            E = 'E' in md['flags']
            T = int(md['time'])
            if md['data']:
                D = [int(x, 16) for x in md['data'].split(',')]
            else:
                D = []
            m = self.msg_class()
            m.id = ID
            m.extended = E
            m.time = self.gettime()
            m.data = D
            m.cortex_time = int(T & 0x00FFFFFF)
            m.cortex_num = int((T >> 24) & 0xFF)
            m.cortex_channel = C
            if m.type == canmsg.TYPE_IN:
                old = self.last_msg.get(m.cortex_channel, -1)
                if old != -1:
                    if ((old + 1) & 0xFF) != m.cortex_num:
                        cnt = self.drop_cnt.get(C, 0)
                        cnt += 1
                        self.drop_cnt[C] = cnt
                        self.info(3 + C, 'channel {0:d} dropped {1:<10d}'.format(C, cnt))
                self.last_msg[C] = m.cortex_num
            return m
        return None

    def do_read(self):
        while True:
            try:
                return self.q.get(False)
            except Queue.Empty:
                self.read_socket()

    def do_write(self, m):
        fmt = 'CAN {0:d} {1:X} {2:s} {3:d} {4:s}\n'
        args = (self.channel
                , m.id
                , m.extended and 'E' or 'S'
                , int(m.time * 1e6) % 0xFFFFFFFF
                , ','.join([hex(x) for x in m.data]))
        self.socket.send(fmt.format(*args))

    def message_handler(self, m):
        self.log(m)
        if not m.sent and (m.addr == 0x4):
            self.info(5, 'pft')
            n = self.msg_class(data=m)
            n.extended = True
            self.write(n)

    def action_handler(self, key):
        if key == 'INIT':
            self.info(6, 'CDC channel {0}'.format(self.channel))
        elif key == 's':
            m = self.msg_class()
            m.id = 1
            m.data = [1,2,3]
            m.extended = True
            self.write(m)

def usage():
    s = 'Usage: {0} -h <server hostname> -p <port number> [-c <ch>]\n'
    s = s.format(sys.argv[0])
    sys.stderr.write(s)
    sys.stderr.write('\twhere ch is 0 by default\n')

def main():
    import interface
    host = None
    port = None
    channel = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:h:p:')
    except getopt.GetoptError, e:
        sys.stderr.write('error: {0}\n'.format(str(e)))
        usage()
        sys.exit(1)
    for o, a in opts:
        if o == '-h':
            host = a
        elif o == '-p':
            port = int(a)
        elif o == '-c':
            channel = int(a)
    if (host == None) or (port == None):
        sys.stderr.write('error: missing argument\n')
        usage()
        sys.exit(1)
    c = CDCChannel(channel, host, port, msg_class=CDCMsg)
    i = interface.Interface(c)
    i.run()

if __name__ == '__main__':
    main()
