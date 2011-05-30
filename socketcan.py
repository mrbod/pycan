#!/usr/bin/env python
import struct
import socket
import fcntl
import array
import canmsg
import canchannel

class SocketCanChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=None, silent=False, msgclass=canmsg.CanMsg):
        self.time_offset = None
        # create CAN socket
        self.socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        # setup id filter
        id = 0
        mask = 0
        self.socket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER, struct.pack("II", id, mask))
        # enable/disable loopback
        loopback = 0
        self.socket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_LOOPBACK, struct.pack("I", loopback))
        # bind to interface "canX" or "any")
        # tuple is (interface, reserved(can_addr))
        self.socket.bind(("can0",))
        super(SocketCanChannel, self).__init__()

    def gettime(self):
        buf = array.array('L', [0, 0])
        SIOCGSTAMP = 35078
        try:
            r = fcntl.ioctl(self.socket, SIOCGSTAMP, buf, 1)
            T = struct.unpack('LL', buf)
            res = T[0] + T[1] / 1000000.0
            if self.time_offset == None:
                self.time_offset = super(SocketCanChannel, self).gettime() - res
            return res + self.time_offset
        except:
            pass
        return super(SocketCanChannel, self).gettime()

    def unpack(self, frame):
        mid, mdlca, mdata = struct.unpack("I4s8s", frame)
        mdlc = ord(mdlca[0])
        data=[ord(x) for x in mdata[:mdlc]]
        return canmsg.CanMsg(id=mid, data=data, time=self.gettime())

    def pack(self, m):
        fill = "\0\0\0\0\0\0\0\0"
        dlc = m.dlc()
        dlca = chr(dlc) + "\0\0\0"
        data = ''.join([chr(c) for c in m.data]) + chr(0) * (8 - dlc)
        x = struct.pack("i4s8s", m.id, dlca, data)
        return x

    def do_read(self):
        cf, addr = self.socket.recvfrom(16)
        m = self.unpack(cf)
        m.time = self.gettime()
        return m

    def do_write(self, m):
        d = self.pack(m)
        self.socket.send(d)
        m.time = self.gettime()

if __name__ == '__main__':
    c = SocketCanChannel()
    while True:
        print c.read()

