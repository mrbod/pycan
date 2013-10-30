#!/usr/bin/env python
import sys
import re
import time
import socket
import datetime
import getopt
import threading

class BRSC(object):
    def __init__(self, channel=-1, bitrate=125000, hostname='localhost', port=5555):
        self.channel = channel
        self.bitrate = bitrate
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((hostname, port))
        s = 'BRSC STANDBY {0:d} {1:d}\n'.format(self.channel, self.bitrate)
        self.socket.send(s)
        time.sleep(1)
        r = self.socket.recv(4096)
        if r != s:
            sys.stderr.write('Failed to start cdcs BRSC:\n')
            sys.stderr.write(r)
            sys.stderr.write('\n')
            self.socket.close()

    def send(self, data):
        self.socket.send(str(data))

    def recv(self):
        r = self.socket.recv(1024)
        if r:
            return r
        return None

def usage():
    s = 'Usage: {0} -h <server hostname> -p <port number> [-c <ch>] [-b <bitrate>]\n'
    s = s.format(sys.argv[0])
    sys.stderr.write(s)
    sys.stderr.write('\twhere ch is 0 by default\n')
    sys.stderr.write('\tif ch < 0 all cdcs traffic will be received\n')

def main():
    host = None
    port = None
    channel = 0
    bitrate = 125000
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:h:p:b:')
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
        elif o == '-b':
            bitrate = int(a)
    if (host == None) or (port == None):
        sys.stderr.write('error: missing argument\n')
        usage()
        sys.exit(1)
    c = BRSC(channel, bitrate, host, port)
    for l in sys.stdin:
        c.send(l)
    time.sleep(1)
    while 1:
        s = c.recv()
        if s:
            sys.stdout.write(s)
            sys.stdout.flush()
        else:
            time.sleep(0.01)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print

