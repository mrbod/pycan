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
    _mfmt = '{0.stcan:<15s} ' + canmsg.CanMsg._mfmt

    def __init__(self, **kwargs):
        super(StCanMsg, self).__init__(**kwargs)

    @property
    def addr(self):
        if self.extended:
            return (self.id >> 3) & 0x00FFFFFF
        else:
            return (self.id >> 3) & 0x3f

    @addr.setter
    def addr(self, a):
        if self.extended:
            if a > 0x00FFFFFF:
                s = 'address(%d) out of range for 29-bit STCAN' % a
                raise ValueError(s)
            self.id = (self.group << 27) | (a << 3) | self.type
        else:
            if a > 0x03F:
                s = 'address(%d) out of range for 11-bit STCAN' % a
                raise ValueError(s)
            self.id = (self.group << 9) | (a << 3) | self.type

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
        return '{0.sgroup:>4s},{0.stype:>3s},{0.saddr}'.format(self)

    @property
    def index(self):
        return self.get_word(0)

    @index.setter
    def index(self, i):
        set_word(0, i)

    def __getattribute__(self, a):
        if (len(a) == 2) and (a[0] in 'wW') and (a[1] in '0123'):
            return self.get_word(int(a[1]))
        return super(StCanMsg, self).__getattribute__(a)

    def __setattr__(self, a, v):
        if (len(a) == 2) and (a[0] in 'wW') and (a[1] in '0123'):
            return self.set_word(int(a[1]), v)
        return super(StCanMsg, self).__setattr__(a, v)

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
    m = StCanMsg(data=[1,2,3,4,5,6,7,8])
    print hex(m.w1), hex(m.W1)
    m.w1 = 0x0908
    print hex(m.w1), hex(m.W1)
    m.extended = False
    try:
        m.addr = 0x3F
        print m
        m.addr = 0x40
    except ValueError, e:
        print e
    m.extended = True
    try:
        m.addr = 0x00FFFFFF
        print m
        m.addr = 0x01000000
    except ValueError, e:
        print e

