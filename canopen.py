#!/bin/env python
import canmsg
import sys
import socketcan

class CanOpenMsg(canmsg.CanMsg):
    __mfmt = '{0.id:03X} {1:<20s} node:{2:02X} {0.time:9.3f} {0.dlc}: {0.data:<32s}'

    def __str__(self):
        fc = self.id & 0x780
        node = self.id & 0x7F
        if fc == 0x00:
            cmd = self.data[0]
            node = self.data[1]
            if cmd == 1:
                desc = 'NMT START'
            elif cmd == 2:
                desc = 'NMT STOP'
            elif cmd == 128:
                desc = 'NMT GOTO PREOP'
            elif cmd == 129:
                desc = 'NMT RESET'
            elif cmd == 130:
                desc = 'NMT RESET COM'
            else:
                desc = 'NMT ????'
        elif fc == 0x80:
            if node == 0:
                if self.dlc == 1:
                    desc = 'SYNC %02X' % self.data[0]
                elif self.dlc == 0:
                    desc = 'SYNC'
                else:
                    desc = 'SYNC????'
            else:
                x = self.data[0] + (self.data[1] * 256)
                desc = 'EMCY 0x%04X' % x
        elif (fc >= 0x180) and (fc < 0x580):
            if (fc & 0x80) > 0:
                desc = 'TPDO'
            else:
                desc = 'RPDO'
        elif (fc >= 0x580) and (fc < 0x680):
            if (fc & 0x80) > 0:
                desc = 'TSDO'
            else:
                desc = 'RSDO'
        elif fc == 0x700:
            x = self.data[0] & 0x7F
            if x == 0:
                desc = 'NMTEC BOOT'
            elif x == 4:
                desc = 'NMTEC STOPPED'
            elif x == 5:
                desc = 'NMTEC OPERATIONAL'
            elif x == 127:
                desc = 'NMTEC PREOPERATIONAL'
            else:
                desc = 'NMTEC ????'
        else:
            desc = '????'
        return self.__mfmt.format(self, desc, node)

def parse_stdin():
    import re
    rmsg = re.compile(r'^\s*(\d+\.\d+)\s+\d\s+(\d+)\s+\w+\s+d\s+(\d)\s(.*)$')
    msg = CanOpenMsg()
    for line in sys.stdin:
        o = rmsg.match(line.strip())
        if o:
            t, id, dlc, data = o.groups()
            msg.data = [int(x, 16) for x in data.split()]
            msg.id = int(id, 16)
            msg.time = float(t)
            sys.stdout.write(str(msg))
            sys.stdout.write('\n')

if __name__ == '__main__':
    #import cProfile
    import interface
    static = False
    for o in sys.argv[1:]:
        if o == '-s':
            static = True
        elif o == '-':
            parse_stdin()
            sys.exit(0)
    c = socketcan.SocketCanChannel(0)
    i = interface.Interface(c, static=static)
    i.run()
    #cProfile.run('i.run()', 'profile')

