import canmsg
EOF = -1
ERROR_PADDING = -2

DLE = 0x10
STX = 0x02
ETX = 0x03

class DLEHandler(object):
    def __init__(self, port):
        self.port = port
        self.got_dle = False
        self.frame = []

    def dle_send(self, byte):
        if byte == DLE:
            self.port.write(DLE)
        self.port.write(byte)

    def send_frame(self, frame):
        for d in frame:
            self.dle_send(d)
        self.port.write(DLE)
        self.port.write(ETX)

    def get_frame(self):
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

    def frame2can(self, frame):
        id = (frame[0] << 8) + frame[1]
        data = frame[2:-1]
        return canmsg.CanMsg(id=id, data=data)

    def can2frame(self, m):
        frame = []
        frame.append((m.id >> 8) & 0xFF)
        frame.append(m.id & 0xFF)
        frame += m.data
        return frame

    def read(self):
        frame = self.get_frame()
        if type(frame) is int:
            if frame == EOF:
                pass
            elif frame == ERROR_PADDING:
                dump_error('ERROR: PADDING')
            else:
                dump_error('ERROR: decode, unknown status(%d)' % frame)
        elif type(frame) is list:
            if len(frame) < 2:
                dump_error('ERROR: LENGTH')
            else:
                try:
                    return self.frame2can(frame)
                except Exception, e:
                    dump_error('ERROR: %s' % str(e))
        else:
            dump_error('ERROR: decode, unknown frame type(%s)' % str(type(frame)))
        return None

    def write(self, msg):
        self.send_frame(self.can2frame(msg))

