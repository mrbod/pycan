#!/usr/bin/env python
import sys
import serial
import time
from canmsg import CanMsg

canOK = 0
canERR_NOMSG = -2

def timestamp():
    return time.time()

class CanSerialChannel(object):
    def __init__(self, comport = 0, bitrate=19200, on_msg=None):
        self.port = serial.Serial(port = comport, baudrate = bitrate)
        self.bitrate = bitrate
        self.on_msg = on_msg
        self.starttime = timestamp()

    def __del__(self):
        pass

    def read(self):
        data = self.port.read(timeout = 0.1)
        if len(data) == 0:
            return None

        self.data += data
        m = self.get_message()
        if m:
            if self.on_msg:
                self.on_msg(m)

    def get_message(self):
        i = self.data.find('\x10\x03')
        if i < 0:
            return None
        s = self.data[:i].replace('\x10\x10','\x10')
        self.data = self.data[i + 2:]
        T = timestamp()
        d = [ord(c) for c in s]
        id = (d[0] << 8) + d[1]
        m = CanMsg(id, d[2:], T - self.starttime, channel=self)
        return m

    def write(self, msg):
        d = ''.join([chr(x) for x in msg.data])
        res = canlib32.canWrite(self.handle, msg.id, d, len(d), msg.flags)
        T = timestamp()
        msg.time = T - self.starttime
        msg.sent = True
        if self.on_msg:
            self.on_msg(msg)

def main():
    ch = CanSerialChannel(int(sys.argv[1]))
    while True:
        m = ch.read()
        while m:
            print m
            m = ch.read()
        sys.stdout.flush()
        time.sleep(0.001)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

