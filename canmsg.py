STCAN_GROUP = ('POUT', 'PIN', 'SEC', 'CFG')
STCAN_TYPE = ('OUT', 'IN', 'UNDEF2', 'UNDEF3', 'UNDEF4', 'MON', 'UNDEF6')
GROUP_POUT = 0
GROUP_PIN = 1
GROUP_SEC = 2
GROUP_CFG = 3
TYPE_OUT = 0
TYPE_IN = 1
TYPE_MON = 5

canMSG_RTR = 0x0001      # Message is a remote request
canMSG_STD = 0x0002      # Message has a standard ID
canMSG_EXT = 0x0004      # Message has an extended ID
canMSG_WAKEUP = 0x0008      # Message to be sent / was received in wakeup mode
canMSG_NERR = 0x0010      # NERR was active during the message
canMSG_ERROR_FRAME = 0x0020      # Message is an error frame
canMSG_TXACK = 0x0040      # Message is a TX ACK (msg is really sent)
canMSG_TXRQ = 0x0080      # Message is a TX REQUEST (msg is transfered to the chip)
canMSGERR_HW_OVERRUN = 0x0200      # HW buffer overrun
canMSGERR_SW_OVERRUN = 0x0400      # SW buffer overrun
canMSGERR_STUFF = 0x0800      # Stuff error
canMSGERR_FORM = 0x1000      # Form error
canMSGERR_CRC = 0x2000      # CRC error
canMSGERR_BIT0 = 0x4000      # Sent dom, read rec
canMSGERR_BIT1 = 0x8000      # Sent rec, read dom

flags_inv = {
        0x0001: 'canMSG_RTR',
        0x0002: 'canMSG_STD',
        0x0004: 'canMSG_EXT',
        0x0008: 'canMSG_WAKEUP',
        0x0010: 'canMSG_NERR',
        0x0020: 'canMSG_ERROR_FRAME',
        0x0040: 'canMSG_TXACK',
        0x0080: 'canMSG_TXRQ',
        0x0200: 'canMSGERR_HW_OVERRUN',
        0x0400: 'canMSGERR_SW_OVERRUN',
        0x0800: 'canMSGERR_STUFF',
        0x1000: 'canMSGERR_FORM',
        0x2000: 'canMSGERR_CRC',
        0x4000: 'canMSGERR_BIT0',
        0x8000: 'canMSGERR_BIT1',
        }

flag_texts = {
        canMSG_RTR: 'RTR',
        canMSG_STD: 'STD',
        canMSG_EXT: 'EXT',
        canMSG_WAKEUP: 'WAKEUP',
        canMSG_NERR: 'NERR',
        canMSG_ERROR_FRAME: 'ERROR_FRAME',
        canMSG_TXACK: 'TXACK',
        canMSG_TXRQ: 'TXRQ',
        canMSGERR_HW_OVERRUN: 'HW_OVERRUN',
        canMSGERR_SW_OVERRUN: 'SW_OVERRUN',
        canMSGERR_STUFF: 'STUFF',
        canMSGERR_FORM: 'FORM',
        canMSGERR_CRC: 'CRC',
        canMSGERR_BIT0: 'BIT0',
        canMSGERR_BIT1: 'BIT1',
        }

class CanMsg(object):
    def __init__(self, id=0, data=[], flags=0, time=0, channel=None, dlc=None, sent=False):
        if isinstance(data, type(self)):
            self.id = data.id
            self.data = [b for b in data.data]
            self.flags = data.flags
        else:
            self.id = id
            self.data = data
            self.flags = flags
        self.time = time
        if isinstance(dlc, int):
            L = len(self.data)
            if L < dlc:
                self.data += (dlc - L) * [0]
            else:
                self.data = self.data[0:dlc]
        self.channel = channel
        self.sent = sent

    def dlc(self):
        return len(self.data) 

    def addr(self):
        return (self.id >> 3) & 0x3f

    def group(self):
        return (self.id >> 9) & 0x3

    def sgroup(self):
        try:
            return STCAN_GROUP[self.group()]
        except:
            return 'GU'

    def sflags(self):
        sf = []
        for k, s in flag_texts.items():
            if (self.flags & k) != 0:
                sf.append(s) 
        return ', '.join(sf)

    def type(self):
        return self.id & 0x7

    def stype(self):
        try:
            return STCAN_TYPE[self.type()]
        except:
            return 'TU'

    def stcan(self):
        return '%4s,%02X,%-3s' % (self.sgroup(), self.addr(), self.stype())

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
        dlc = self.dlc()
        if dlc:
            fmt = '[%02X' + ', %02X' * (dlc - 1) + ']'
            m = fmt % tuple(self.data)
        else:
            m = '[]'
        if self.sent:
            direction = 'W'
        else:
            direction = 'R'
        #fmt = '%s %03X %-15s %8.3f %d:%-32s f:%02X(%s)'
        #args = (direction, self.id, self.stcan(), self.time, dlc, m, self.flags, self.sflags())
        fmt = '%s %03X %-15s %8.3f %d:%-32s'
        args = (direction, self.id, self.stcan(), self.time, dlc, m)
        return fmt % args

    def __repr__(self):
        m = self.__module__
        n = self.__class__.__name__
        f = [self.flags & (1 << x) for x in range(16)]
        f = [flags_inv[x] for x in f if flags_inv.has_key(x)]
        if f:
            f = ' | '.join(['%s.%s' % (m, x) for x in f])
        else:
            f = '0'
        vals = (m, n, self.id, str(self.data), f, self.time)
        return '%s.%s(id=%d, data=%s, flags=%s, time=%d)' % vals

