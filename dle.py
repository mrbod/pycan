#!/bin/env python
EOF = -1
ERROR_PADDING = -2

DLE = 0x10
STX = 0x02
ETX = 0x03

class DLEHandler(object):
    def __init__(self, port):
        self.port = port
        self.get_start = True
        self.got_dle = False
        self.frame = []

    def dle_send(self, byte):
        if byte == DLE:
            self.port.write(DLE)
        self.port.write(byte)

    def send(self, frame):
        cs = 0
        self.port.write(DLE)
        self.port.write(STX)
        for d in frame:
            self.dle_send(d)
        self.port.write(DLE)
        self.port.write(ETX)

    def read(self):
        b = self.port.read()
        while b != EOF:
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
                        return self.frame[:]
                    elif b == DLE:
                        self.frame.append(b)
                    elif b == STX:
                        self.frame = []
                    else:
                        self.get_start = True
                        return ERROR_PADDING
                elif b == DLE:
                    self.got_dle = True
                else:
                    self.frame.append(b)
            b = self.port.read()
        return EOF

def main():
    import sys
    class Port(object):
        def read(self):
            c = ord(sys.stdin.read(1))
            return c

    h = DLEHandler(Port())
    while True:
        r = h.read()
        if r not in (EOF, ERROR_PADDING):
            if r[0] == 0xFF:
                id = ''.join(['%02X' % d for d in r[1:3]])
                data = ['%02X' % d for d in r[3:-1]]
                cs = '%02X' % r[-1]
                print id, data, cs
            elif r[0] == 0xFE:
                id = ''.join(['%02X' % d for d in r[1:5]])
                data = ['%02X' % d for d in r[5:-1]]
                cs = '%02X' % r[-1]
                print id, data, cs
            elif r[0] == 0x01:
                print 'ACK'
        else:
            print r, dir(r)

if __name__ == '__main__':
    main()
