#!/usr/bin/env python
import sys
import re
import canmsg
import canchannel

class CanDumpChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=None, silent=False, msgclass=canmsg.CanMsg):
        super(CanDumpChannel, self).__init__()
        self.linere = re.compile(r'<(.*)> \[(\d)\] (.*)')
        self.msgclass = msgclass

    def do_read(self):
        l = sys.stdin.readline()
        o = self.linere.search(l)
        if o:
            m = self.msgclass()
            m.id = int(o.group(1), 16)
            m.data = [int(x, 16) for x in o.group(3).split()]
            if m.dlc() != int(o.group(2)):
                raise Exception('DLC <-> data missmatch')
            m.time = self.gettime()
            return m
        return None

    def do_write(self, m):
        pass

if __name__ == '__main__':
    c = CanDumpChannel()
    while True:
        print c.read()

