STCAN_GROUP = ('POUT', 'PIN', 'SEC', 'CFG')
STCAN_TYPE = ('OUT', 'IN', 'UNDEF2', 'UNDEF3', 'UNDEF4', 'MON', 'UNDEF6')

class CanMsg(object):
    def __init__(self, id = 0, msg = [], flags = 0, time = 0):
        self.id = id
        self.flags = flags
        self.time = time
        self.msg = msg

    def dlc(self):
        return len(self.msg) 

    def addr(self):
        return (self.id >> 3) & 0x3f

    def group(self):
        return (self.id >> 9) & 0x3

    def sgroup(self):
        return STCAN_GROUP[self.group()]

    def type(self):
        return self.id & 0x7

    def stype(self):
        return STCAN_TYPE[self.type()]

    def stcan(self):
        return '%4s,%02X,%-3s' % (self.sgroup(), self.addr(), self.stype())

    def __str__(self):
        t = self.time / 1000.0
        dlc = self.dlc()
        if dlc:
            fmt = '[%02X' + ', %02X' * (dlc - 1) + ']'
            m = fmt % tuple(self.msg)
        else:
            m = '[]'
        fmt = '%03X %s %8.3f %d:%-32s f:%02X'
        args = (self.id, self.stcan(), t, dlc, m, self.flags)
        return fmt % args
