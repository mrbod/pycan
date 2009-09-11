EOF = -1
ERROR_PADDING = -2

DLE = 0x10
ETX = 0x03

class VBGDLEHandler(object):
    def __init__(self, port):
        self.port = port
        self.got_dle = False
        self.frame = []

    def dle_send(self, byte):
        if byte == DLE:
            self.port.write(DLE)
        self.port.write(byte)

    def send(self, frame):
        for d in frame:
            self.dle_send(d)
        self.port.write(DLE)
        self.port.write(ETX)

    def read(self):
        b = self.port.read()
        while b != EOF:
            if self.got_dle:
                self.got_dle = False
                if b == ETX:
                    f = self.frame[:]
                    self.frame = []
                    return f
                elif b == DLE:
                    self.frame.append(b)
                else:
                    return ERROR_PADDING
            elif b == DLE:
                self.got_dle = True
            else:
                self.frame.append(b)
            b = self.port.read()
        return EOF

