#!/usr/bin/env python
import struct
import socket
import select
import fcntl
import array
import canmsg
import canchannel

class SocketCanChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=None, silent=False, msg_class=canmsg.CanMsg):
        self.time_offset = None
        # create CAN socket
        self.socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        # select 
        self.poll = select.poll()
        self.poll.register(self.socket.fileno(), select.POLLIN)
        # setup id filter
        id = 0
        mask = 0
        self.socket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER, struct.pack("II", id, mask))
        # enable/disable loopback
        loopback = 0
        self.socket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_LOOPBACK, struct.pack("I", loopback))
        # bind to interface "canX" or "any")
        # tuple is (interface, reserved(can_addr))
        cani = 'can{0}'.format(channel)
        self.socket.bind((cani,))
        super(SocketCanChannel, self).__init__(msg_class=msg_class)

    def gettime(self):
        try:
            # fetch struct timeval
            SIOCGSTAMP = 35078
            buf = array.array('L', [0, 0])
            r = fcntl.ioctl(self.socket, SIOCGSTAMP, buf, 1)
            T = struct.unpack('LL', buf)
            res = T[0] + T[1] / 1000000.0
            if self.time_offset == None:
                self.time_offset = super(SocketCanChannel, self).gettime() - res
            res = res + self.time_offset
        except:
            res = super(SocketCanChannel, self).gettime()
        return res

    def unpack(self, frame):
        mid, mdlca, mdata = struct.unpack("I4s8s", frame)
        mdlc = ord(mdlca[0])
        data=[ord(x) for x in mdata[:mdlc]]
        return self.msg_class(id=mid, data=data, time=self.gettime())

    def pack(self, m):
        dlc = m.dlc()
        dlca = chr(dlc) + "\0\0\0"
        data = ''.join([chr(c) for c in m.data]) + chr(0) * (8 - dlc)
        x = struct.pack("i4s8s", m.id, dlca, data)
        return x

    def do_read(self):
        if self.poll.poll(100):
            cf, addr = self.socket.recvfrom(16)
            m = self.unpack(cf)
            m.time = self.gettime()
            return m
        return None

    def do_write(self, m):
        d = self.pack(m)
        self.socket.send(d)
        m.time = self.gettime()

if __name__ == '__main__':
    import interface
    c = SocketCanChannel()
    i = interface.Interface(c)
    i.run()

