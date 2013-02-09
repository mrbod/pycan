#!/bin/env python
import sys
import time
import StringIO

EOF = -1
ERROR_PADDING = -2

DLE = 0x10
STX = 0x02
ETX = 0x03

class FilePort(object):
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile

    def read(self):
        if self.infile == None:
            return EOF
        c = self.infile.read(1)
        if c == '':
            return EOF
        return ord(c)

    def write(self, c):
        if self.outfile == None:
            return
        if c != None:
            self.outfile.write(chr(c))

class StdIOPort(FilePort):
    def __init__(self):
        FilePort.__init__(self, sys.stdin, sys.stdout)

class DLEHandler(object):
    def __init__(self, port=None):
        if port != None:
            self.port = port
        else:
            self.port = StdIOPort()
        self.get_start = True
        self.got_dle = False
        self.frame_reset()
        self.rx = 0

    def dle_send(self, byte):
        if byte == DLE:
            self.port.write(DLE)
        self.port.write(byte)

    def send(self, frame):
        if isinstance(frame, str):
            frame = [ord(c) for c in frame]
        self.port.write(DLE)
        self.port.write(STX)
        for d in frame:
            self.dle_send(d)
        self.port.write(DLE)
        self.port.write(ETX)

    def frame_reset(self):
        self.frame = []

    def frame_add(self, byte):
        self.frame.append(byte)

    def dump_frame(self):
        sys.stderr.write('FRAME so far: %s\n' % str(self.frame))

    def error(self, txt):
        sys.stderr.write('ERROR at byte %d(0x%08X):  %s\n' % (self.rx, self.rx, txt))

    def read(self):
        b = self.port.read()
        while b != EOF:
            self.rx += 1
            if self.get_start:
                if self.got_dle:
                    self.got_dle = False
                    if b == STX:
                        self.get_start = False
                        self.frame_reset()
                    else:
                        self.error('get_start, expected STX, got <0x%02X>' % b)
                else:
                    if b == DLE:
                        self.got_dle = True
                    else:
                        self.error('get_start, expected DLE, got <0x%02X>' % b)
            else:
                if self.got_dle:
                    self.got_dle = False
                    if b == ETX:
                        self.get_start = True
                        #return ''.join([chr(x) for x in self.frame])
                        return self.frame
                    elif b == DLE:
                        self.frame_add(b)
                    elif b == STX:
                        self.error('get_data, expected ETX, got STX')
                        self.dump_frame()
                        self.frame_reset()
                        return ERROR_PADDING
                    else:
                        self.error('get_data, expected ETX, got <0x%02X>' % b)
                        self.dump_frame()
                        self.get_start = True
                        return ERROR_PADDING
                elif b == DLE:
                    self.got_dle = True
                else:
                    self.frame_add(b)
            b = self.port.read()
        return EOF

def encode(s):
    f = StringIO.StringIO()
    p = FilePort(None, f)
    h = DLEHandler(p)
    h.send(s)
    f.seek(0)
    return f.read()

def decode(s):
    f = StringIO.StringIO(s)
    p = FilePort(f, None)
    h = DLEHandler(p)
    r = h.read()
    return r

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

