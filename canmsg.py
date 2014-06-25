#!/usr/bin/env python
import re

class CanMsgException(Exception):
    pass

STCAN_GROUP = ('POUT', 'PIN', 'SEC', 'CFG')
STCAN_TYPE = ('OUT', 'IN', '???', '???', '???', 'MON', '???', '???')
GROUP_POUT = 0
GROUP_PIN = 1
GROUP_SEC = 2
GROUP_CFG = 3
TYPE_OUT = 0
TYPE_IN = 1
TYPE_MON = 5

FORMAT_STD = 0
FORMAT_STCAN = 1

std_fmt = '{0.sid:>8} {0.time:9.3f} {0.dlc}: {0.data:s}'
stcan_fmt = '{0.stcan:<15s} ' + std_fmt

data_fmt = '{0:02X}'

formats = [std_fmt, stcan_fmt]

format_index = FORMAT_STD
msg_fmt = formats[format_index]

def format_set(fmt):
    global msg_fmt, format_index
    try:
        msg_fmt = formats[fmt]
        format_index = fmt
    except:
        format_index = FORMAT_STD
        msg_fmt = formats[format_index]

def format_rotate():
    global format_index
    format_index += 1
    format_set(format_index)

def data_parser(s):
    if len(s) == 0:
        return []
    return [int(x, 0) for x in s.split(',')]

class Data(bytearray):
    def __init__(self, data):
        if type(data) is str:
            data = data_parser(data)
        super(Data, self).__init__(data)
        self.dlc = len(self)

    def __str__(self):
        t = (data_fmt.format(d) for d in self)
        return ', '.join(t)

class CanMsg(object):
    __slots__ = ('can_id', 'xx_data', 'xx_extended'
            , 'time', 'channel', 'sent', 'error_frame')

    def __init__(self, can_id=0, data=[], extended=False, time=0.0
            , channel=None, sent=False, error_frame=False):
        super(CanMsg, self).__init__()
        if isinstance(data, type(self)):
            self.can_id = data.can_id
            self.data = [b for b in data.data]
            self.extended = data.extended
            self.time = data.time
        else:
            self.can_id = can_id
            self.data = data
            self.extended = extended
            self.time = time
        self.channel = channel
        self.sent = sent
        self.error_frame = error_frame

    @staticmethod
    def format_set(cls, fmt):
        format_set(fmt)

    @staticmethod
    def format_rotate(cls):
        format_rotate()

    @property
    def sid(self):
        if self.xx_extended:
            return '{0:08X}'.format(self.can_id)
        return '{0:03X}'.format(self.can_id)

    @property
    def extended(self):
        return self.xx_extended

    @extended.setter
    def extended(self, e):
        if e:
            self.xx_extended = True
        else:
            self.xx_extended = False

    @property
    def dlc(self):
        return self.xx_data.dlc

    @property
    def data(self):
        return self.xx_data

    @data.setter
    def data(self, data):
        self.xx_data = Data(data)

    @property
    def ssent(self):
        if self.sent:
            return 'W'
        return 'R'

    @property
    def addr(self):
        if self.extended:
            return (self.can_id >> 3) & 0x00FFFFFF
        else:
            return (self.can_id >> 3) & 0x3f

    @addr.setter
    def addr(self, a):
        if self.extended:
            if a > 0x00FFFFFF:
                s = 'address(%d) out of range for 29-bit STCAN' % a
                raise ValueError(s)
            self.can_id = (self.group << 27) | (a << 3) | self.type
        else:
            if a > 0x03F:
                s = 'address(%d) out of range for 11-bit STCAN' % a
                raise ValueError(s)
            self.can_id = (self.group << 9) | (a << 3) | self.type

    @property
    def saddr(self):
        if self.extended:
            return '{0.addr:06X}'.format(self)
        return '{0.addr:02X}'.format(self)

    @property
    def group(self):
        if self.extended:
            return (self.can_id >> 27) & 0x3
        else:
            return (self.can_id >> 9) & 0x3

    @group.setter
    def group(self, g):
        if self.extended:
            self.can_id = (self.can_id & 0x07FFFFFF) | (g << 27)
        else:
            self.can_id = (self.can_id & 0x1FF) | (g << 9)

    @property
    def sgroup(self):
        return STCAN_GROUP[self.group]

    @property
    def type(self):
        return self.can_id & 0x7

    @type.setter
    def type(self, t):
        self.can_id = (self.can_id & 0xFFFFFFF8) | t

    @property
    def stype(self):
        return STCAN_TYPE[self.type]

    @property
    def stcan(self):
        return '{0.sgroup:<4s} {0.stype:<3s} {0.saddr}'.format(self)

    @property
    def index(self):
        return self.get_word(0)

    @index.setter
    def index(self, i):
        set_word(0, i)

    def __getattribute__(self, a):
        if (len(a) == 2) and (a[0] in 'wW') and (a[1] in '0123'):
            return self.get_word(int(a[1]))
        return super(CanMsg, self).__getattribute__(a)

    def __setattr__(self, a, v):
        if (len(a) == 2) and (a[0] in 'wW') and (a[1] in '0123'):
            return self.set_word(int(a[1]), v)
        return super(CanMsg, self).__setattr__(a, v)

    def get_word(self, index):
        d = self.data
        s = 2 * index
        return (d[s] << 8) + d[s+1]

    def set_word(self, index, word):
        d = self.data
        s = 2 * index
        d[s] = (word >> 8) & 0xFF
        d[s+1] = word & 0xFF

    def __str__(self):
        if self.error_frame:
            return 'ERROR FRAME'
        return msg_fmt.format(self)

    def __eq__(self, other):
        if not other:
            return False
        if self.can_id != other.can_id:
            return False
        if len(self.xx_data) != len(other.xx_data):
            return False
        for i in range(len(self.xx_data)):
            if self.xx_data[i] != other.xx_data[i]:
                return False
        if self.xx_extended != other.xx_extended:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_biscan(cls, s):
        o = biscan_re.match(s)
        if not o:
            raise CanMsgException('Not a frame: ' + s)
        channel = int(o.group(1))
        time = float(o.group(2).replace(',', '.'))
        can_id = int(o.group(3), 16)
        d = o.group(4)
        if len(d) > 0:
            d = d.split(', ')
            data = [int(x, 16) for x in d]
        else:
            data = []
        return cls(can_id=can_id, time=time, data=data, channel=channel)

    @classmethod
    def from_magnus(cls, s):
        data = s.strip().split(None, 7)
        can_id = int(data[5], 16)
        time = int(data[4]) / 1000.0
        data = [int(x, 16) for x in data[-1].split()]
        return cls(can_id=can_id, time=time, data=data)


    @classmethod
    def from_vector(cls, s):
        o = vector_re.match(s)
        if not o:
            raise CanMsgException('Not a frame: ' + s)
        channel = int(o.group(2))
        time = float(o.group(1))
        can_id = int(o.group(3), 16)
        d = o.group(5)
        if len(d) > 0:
            data = [int(x, 16) for x in d.strip().split()]
        else:
            data = []
        return cls(can_id=can_id, time=time, data=data, channel=channel)

vector_re = re.compile(r'\s*(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]+)x\s+Rx\s+d\s(\d+)((?:\s+[0-9A-F]{2})*)\s+')
biscan_re = re.compile(r'(\d+)\s+\d+\s+(\d+,\d+)\s+\w+\s+([0-9A-Fa-f]+)\s+\d\s+\[\s*([^]]*)\]')

def translate(f):
    trs = (CanMsg.from_vector, CanMsg.from_biscan)
    tr = None
    done = False
    def reader(f):
        while not done:
            l = f.readline()
            if l:
                yield l
            else:
                return
    for i, l in enumerate(reader(f)):
        for tr in trs:
            try:
                yield tr(l)
                done = True
                break
            except CanMsgException as e:
                pass
    else:
        if not done:
            raise CanMsgException('No working translator found for input\n')
    for l in f:
        try:
            yield tr(l)
        except CanMsgException as e:
            pass

if __name__ == '__main__':
    import sys
    if not sys.stdin.isatty():
        for m in translate(sys.stdin):
            print m
    else:
        m = CanMsg()
        m.data = [1,2,3,4]
        print m

