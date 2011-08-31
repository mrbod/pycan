#!/usr/bin/env python
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

class Data(list):
    __fmt1 = '{0:02X}'

    def __init__(self, data):
        super(Data, self).__init__(data)

    def __str__(self):
        t = [self.__fmt1.format(d) for d in self]
        return ', '.join(t)

class CanMsg(object):
    __mfmt = '{0.id:8X} {0.time:9.3f} {0.dlc}: {0.data:<32s}'

    def __init__(self, id=0, data=[], extended=False, time=0.0, channel=None, sent=False):
        if isinstance(data, type(self)):
            self.id = data.id
            self.data = Data([b for b in data.__data])
            self.extended = data.extended
        else:
            self.id = id
            self.data = Data(data)
            self.extended = extended
        self.dlc = len(self.data)
        self.time = time
        self.channel = channel
        self.sent = sent

    def set_data(self, data):
        self.data = Data(data)
        self.dlc = len(self.data)

    def __str__(self):
        return self.__mfmt.format(self)

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
        return '%s.%s(id=%d, data=[%s], flags=%s, time=%d)' % vals

    def __eq__(self, other):
        if not other:
            return False
        if self.id != other.id:
            return False
        if len(self.data) != len(other.data):
            return False
        for i in range(len(self.data)):
            if self.data[i] != other.data[i]:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

if __name__ == '__main__':
    m = CanMsg()
    print m.__sizeof__()
    print dir(m)
