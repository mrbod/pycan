STCAN_GROUP = ('POUT', 'PIN', 'SEC', 'CFG')
STCAN_TYPE = ('OUT', 'IN', 'UNDEF2', 'UNDEF3', 'UNDEF4', 'MON', 'UNDEF6')

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

flag_texts = {canMSG_RTR: 'RTR', canMSG_STD: 'STD', canMSG_EXT: 'EXT', canMSG_WAKEUP: 'WAKEUP', canMSG_NERR: 'NERR', canMSG_ERROR_FRAME: 'ERROR_FRAME', canMSG_TXACK: 'TXACK', canMSG_TXRQ: 'TXRQ', canMSGERR_HW_OVERRUN: 'HW_OVERRUN', canMSGERR_SW_OVERRUN: 'SW_OVERRUN', canMSGERR_STUFF: 'STUFF', canMSGERR_FORM: 'FORM', canMSGERR_CRC: 'CRC', canMSGERR_BIT0: 'BIT0', canMSGERR_BIT1: 'BIT1'}

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

    def __str__(self):
        t = self.time / 1000.0
        dlc = self.dlc()
        if dlc:
            fmt = '[%02X' + ', %02X' * (dlc - 1) + ']'
            m = fmt % tuple(self.msg)
        else:
            m = '[]'
        fmt = '%03X %s %8.3f %d:%-32s f:%02X(%s)'
        args = (self.id, self.stcan(), t, dlc, m, self.flags, self.sflags())
        return fmt % args
