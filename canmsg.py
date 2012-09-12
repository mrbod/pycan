#!/usr/bin/env python
import re

class Data(list):
    __fmt1 = '{0:02X}'

    def __init__(self, data):
        super(Data, self).__init__(data)
        self.dlc = len(self)

    def __str__(self):
        t = [self.__fmt1.format(d) for d in self]
        return ', '.join(t)

class CanMsg(object):
    _mfmt = '{0.sid} {0.time:9.3f} {0.dlc}: {0.data:s}'
    _sre = re.compile(r'(?P<id>[0-9a-fA-F]+)(?P<ext>[ES])?\s+(?:\D\S+\s+)?(?P<time>\d+\.\d+)\s+(?P<dlc>\d):\s*(?P<data>(?:\d\d(?:,\s\d\d)*)?)')

    def __init__(self, id=0, data=[], extended=False, time=0.0, channel=None, sent=False):
        if isinstance(data, type(self)):
            self.id = data.id
            self.data = [b for b in data.__data]
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
        self._extened = e

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

    @classmethod
    def from_str(cls, s, m=None):
        o = cls._sre.match(s)
        if o:
            sid = o.group('id')
            ID = int(sid, 16)
            E = len(sid) > 3
            T = float(o.group('time'))
            D = [int(x, 16) for x in o.group('data').split(', ')]
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
    print m.__sizeof__()
    print dir(m)

