#!/bin/env python
import canmsg
import sys
import re

STCAN_GROUP = ('POUT', 'PIN', 'SEC', 'CFG')
STCAN_TYPE = ('OUT', 'IN', 'UD2', 'UD3', 'UD4', 'MON', 'UD6', 'UD7')
GROUP_POUT = 0
GROUP_PIN = 1
GROUP_SEC = 2
GROUP_CFG = 3
TYPE_OUT = 0
TYPE_IN = 1
TYPE_MON = 5

class StCanMsg(canmsg.CanMsg):
    _mfmt = '{0.sid:>8s} {0.stcan:^15s} {0.time:9.3f} {0.dlc}: {0.data:s}'

    @property
    def addr(self):
        if self.extended:
            return (self.id >> 3) & 0x00FFFFFF
        else:
            return (self.id >> 3) & 0x3f

    @property
    def saddr(self):
        if self.extended:
            return '{0.addr:06X}'.format(self)
        return '{0.addr:02X}'.format(self)

    @property
    def group(self):
        if self.extended:
            return (self.id >> 27) & 0x3
        else:
            return (self.id >> 9) & 0x3

    @property
    def sgroup(self):
        try:
            return STCAN_GROUP[self.group]
        except:
            return '**'

    @property
    def type(self):
        return self.id & 0x7

    @property
    def stype(self):
        try:
            return STCAN_TYPE[self.type]
        except:
            return '**'

    @property
    def stcan(self):
        return '{0.sgroup:>4s},{0.saddr},{0.stype:<3s}'.format(self)

    def get_word(self, index):
        d = self.data
        s = 2 * index
        return (d[s] << 8) + d[s+1]

    def set_word(self, index, word):
        d = self.data
        s = 2 * index
        d[s] = (word >> 8) & 0xFF
        d[s+1] = word & 0xFF

if __name__ == '__main__':
    m = CanMsg()
    print m.__sizeof__()
    print dir(m)
    print m

