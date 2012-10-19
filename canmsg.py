#!/usr/bin/env python
import re

class Data(list):
    __fmt1 = '{0:02X}'

    def __init__(self, data):
        super(Data, self).__init__(data)
        self.dlc = len(self)

    def __str__(self):
        t = (self.__fmt1.format(d) for d in self)
        return ', '.join(t)

class CanMsg(object):
    _mfmt = '{0.sid:>8} {0.time:9.3f} {0.dlc}: {0.data:s}'
    _sre = re.compile(r'\s*(?P<id>[0-9a-fA-F]+)?\s+(?P<time>\d+\.\d+)\s+(?P<dlc>\d):\s*(?P<data>(?:[0-9a-fA-F]{2}(?:,\s[0-9a-fA-F]{2})*)?)')

    def __init__(self, id=0, data=[], extended=False, time=0.0, channel=None, sent=False):
        if isinstance(data, type(self)):
            self.id = data.id
            self.data = [b for b in data.data]
            self.extended = data.extended
            self.time = data.time
        else:
            self.id = id
            self.data = data
            self.extended = extended
            self.time = time
        self.channel = channel
        self.sent = sent

    @property
    def sid(self):
        if self._extened:
            return '{0:08X}'.format(self.id)
        return '{0:03X}'.format(self.id)

    @property
    def extended(self):
        return self._extened

    @extended.setter
    def extended(self, e):
        if e:
            self._extened = True
        else:
            self._extened = False

    @property
    def dlc(self):
        return self._data.dlc

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = Data(data)

    @property
    def ssent(self):
        if self.sent:
            return 'W'
        return 'R'

    def __getattribute__(self, a):
        if (len(a) == 2) and (a[0] in 'dD') and (a[1] in '01234567'):
            return self.data[int(a[1])]
        return super(CanMsg, self).__getattribute__(a)

    def __setattr__(self, a, v):
        if (len(a) == 2) and (a[0] in 'wW') and (a[1] in '0123'):
            return self.set_word(int(a[1]), v)
        return super(CanMsg, self).__setattr__(a, v)


    @classmethod
    def from_str(cls, s, m=None):
        o = cls._sre.match(s)
        if o:
            md = o.groupdict()
            sid = md['id']
            ID = int(sid, 16)
            E = len(sid) > 3
            T = float(md['time'])
            if md['data']:
                D = [int(x, 16) for x in md['data'].split(', ')]
            else:
                D = []
            if m:
                m.id = ID
                m.extended = E
                m.time = T
                m.data = D
            else:
                m = cls(id=ID, extended=E, time=T, data=D)
            return m
        return None

    def __str__(self):
        return self._mfmt.format(self)

    def __eq__(self, other):
        if not other:
            return False
        if self.id != other.id:
            return False
        if len(self._data) != len(other._data):
            return False
        for i in range(len(self._data)):
            if self._data[i] != other._data[i]:
                return False
        if self._extened != other._extened:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

if __name__ == '__main__':
    m = CanMsg()
    m.data = [1,2,3,4]
    print m
    print m.d2
    print m.data[5]

