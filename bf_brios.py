#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

class BRIOSCAN(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, bitrate=kvaser.canBITRATE_125K, silent=False):
        kvaser.KvaserCanChannel.__init__(self, channel=channel, bitrate=bitrate, silent=silent)

    def action_handler(self, c):
        pass

    def message_handler(self, m):
        print(m)

    def exit_handler(self):
        pass

    def dump_msg(self, m):
        fmt = '{0:8.3f} {1:03X} {2:d}:{3:s}\n'
        s = fmt.format(m.time, m.can_id, m.dlc(), m.data_str())
        sys.stdout.write(s)

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

if __name__ == '__main__':
    opts, args = kvaser.parse_args()
    c = BRIOSCAN(channel=opts.channel, bitrate=opts.bitrate, silent=opts.silent)
    kvaser.main(c)
