#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser
import interface

class CanOpen(kvaser.KvaserCanChannel):
    def __init__(self, ch=0, silent=False):
        br = kvaser.canBITRATE_100K
        super(CanOpen, self).__init__(channel=ch, bitrate=br, silent=silent)

    def action_handler(self, c):
        pass

    def message_handler(self, m):
        dlc = m.dlc()
        fc = m.id & 0x780
        node = m.id & 0x7F
        if fc == 0x00:
            cmd = m.data[0]
            node = m.data[1]
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
                if dlc == 1:
                    desc = 'SYNC %02X' % m.data[0]
                elif dlc == 0:
                    desc = 'SYNC'
                else:
                    desc = 'SYNC????'
            else:
                x = m.data[0] + (m.data[1] * 256)
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
            x = m.data[0] & 0x7F
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
        d = m.data_str()
        fmt = '%03X %-20s node:%02X %9.3f %d%-32s'
        args = (m.id, desc, node, m.time, dlc, d)
        self.log(fmt % args)

if __name__ == '__main__':
    silent = False
    for o in sys.argv[1:]:
        if o == '-s':
            silent = True
    channel = CanOpen(0, silent=silent)
    interface = interface.Interface(channel)
    interface.run()

