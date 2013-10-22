#!/bin/env python
import sys
import kvaser
import canmsg

class Monitor(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, silent=False, bitrate=kvaser.canBITRATE_125K):
        kvaser.KvaserCanChannel.__init__(self, silent=silent, channel=channel, bitrate=bitrate)

    def action_handler(self, c):
        m = canmsg.CanMsg()
        m.can_id = (canmsg.GROUP_PIN << 9) | canmsg.TYPE_MON
        m.data = [ord(c)]
        self.write(m)

    def message_handler(self, m):
        if m.type() == canmsg.TYPE_MON:
            sys.stdout.write(chr(m.data[0]))
        else:
            print m

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

if __name__ == '__main__':
    try:
        opts, args = kvaser.parse_args()
        c = Monitor(channel=opts.channel, bitrate=opts.bitrate, silent=opts.silent)
        kvaser.main(c)
    except KeyboardInterrupt:
        pass
