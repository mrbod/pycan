#!/bin/env python
import sys
import time

EOF = -1
ERROR_PADDING = -2

DLE = 0x10
STX = 0x02
ETX = 0x03

class StdIOPort(object):
    def read(self):
        c = sys.stdin.read(1)
        if c == '':
            return EOF
        return ord(c)

    def write(self, c):
        if c != None:
            sys.stdout.write(chr(c))

class DLEHandler(object):
    def __init__(self, port=None):
        if port:
            self.port = port
        else:
            self.port = StdIOPort()
        self.get_start = True
        self.got_dle = False
        self.frame_reset()

    def dle_send(self, byte):
        if byte == DLE:
            self.port.write(DLE)
        self.port.write(byte)

    def send(self, frame):
        self.port.write(DLE)
        self.port.write(STX)
        for d in frame:
            self.dle_send(d)
        self.port.write(DLE)
        self.port.write(ETX)
        self.port.write(None)

    def frame_reset(self):
        self.frame = []

    def frame_add(self, byte):
        self.frame.append(byte)

    def read(self):
        b = self.port.read()
        while b != EOF:
            if self.get_start:
                if self.got_dle:
                    self.got_dle = False
                    if b == STX:
                        self.get_start = False
                        self.frame_reset()
                else:
                    if b == DLE:
                        self.got_dle = True
            else:
                if self.got_dle:
                    self.got_dle = False
                    if b == ETX:
                        self.get_start = True
                        return self.frame
                    elif b == DLE:
                        self.frame_add(b)
                    elif b == STX:
                        self.frame_reset()
                    else:
                        self.get_start = True
                        return ERROR_PADDING
                elif b == DLE:
                    self.got_dle = True
                else:
                    self.frame_add(b)
            b = self.port.read()
        return EOF

def main():
    decode = True
    for a in sys.argv[1:]:
        if a == '-d':
            decode = True
        elif a == '-e':
            decode = False
    h = DLEHandler()
    if decode:
        T0 = time.time()
        while True:
            r = h.read()
            if r == EOF:
                break
            elif r == ERROR_PADDING:
                sys.stderr.write('ERROR_PADDING\n')
                sys.stderr.flush()
            else:
                T = time.time()
                s = '[' + ', '.join(['%02X' % x for x in r]) + ']\n'
                s = '%8.3f %s' % (T - T0, s)
                sys.stdout.write(s)
                sys.stdout.flush()
    else:
        for l in sys.stdin:
            frame =  l.strip()
            if frame:
                frame = [int(''.join(x), 16) for x in zip(frame[0::2], frame[1::2])]
                h.send(frame)

if __name__ == '__main__':
    main()
