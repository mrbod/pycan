#!/bin/env python
import canmsg
import sys
import socketcan
import threading
import time
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

class StCanMsg(canmsg.CanMsg):
    _mfmt = '{0.sid} {0.stcan:s} {0.time:9.3f} {0.dlc}: {0.data:s}'

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

class StCanChannel(socketcan.SocketCanChannel):
    def __init__(self, channel=0, primary_size=0, address=0):
        self.message_queue = []
        self.state = 'IDLE'
        self.address = address
        self.row_action = 6
        self.row_info = 7
        self.row_index = 2
        self.row_value = self.row_index + 1
        self.index = 0
        self.value = 0
        self.primary_answer = False
        self.send_primary = False
        id = (self.address << 3)
        self.primary = StCanMsg(id=id, data=primary_size*[0])
        self.exception = None
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.thread.start()
        super(StCanChannel, self).__init__(channel=channel, msg_class=StCanMsg)

    def __del__(self):
        self.close()

    def close(self):
        self.run_thread = False
        self.thread.join()
        super(StCanChannel, self).close()

    def run(self):
        try:
            time.sleep(1.0)
            self.info(self.row_info, '(i)ndex, (v)alue, (t)oggle')
            while self.run_thread:
                if self.send_primary:
                    self.send_primary = False
                    m = StCanMsg()
                    m.id = self.primary.id
                    m.data = self.primary.data
                    self.write(m)
                elif len(self.message_queue) > 0:
                    m = self.message_queue.pop(0)
                    self.write(m)
                else:
                    time.sleep(0.100)

        except Exception, e:
            self.exception = e
            raise

    def send(self, m):
        self.message_queue.append(m)

    def info(self, row, txt):
        super(StCanChannel, self).info(row, '{0:<80s}'.format(txt))

    def toggle(self, index):
        B = index / 8
        b = index % 8
        mask = 1 << b
        if B < self.primary.dlc:
            d = self.primary.data[B]
            if d & mask:
                d = d & ~mask
                self.info(self.row_action, 'bit{0.index:d} 1->0'.format(self))
            else:
                d = d | mask
                self.info(self.row_action, 'bit{0.index:d} 0->1'.format(self))
            self.primary.data[B] = d
        else:
            self.info(self.row_action, 'primary index out of range {0}'.format(index))

    def edit_value(self, c, val):
        if c in '0123456789':
            try:
                x = int(c)
                val = val * 10 + int(c)
            except:
                pass
        elif (c == chr(0x08)) or (c == chr(0x7F)): # BS or DEL
            val = val / 10
        return val

    def action_handler(self, c):
        if self.state == 'IDLE':
            if c == 'p':
                self.send_primary = True
            elif c == 'P':
                self.primary_answer = not self.primary_answer
            elif c == 'i':
                self.state = 'INDEX'
            elif c == 'v':
                self.state = 'VALUE'
            elif c == 't':
                self.toggle(self.index)
        elif (c == chr(0x0A)) or (c == chr(0x0D)): # LF or CR
            self.state = 'IDLE'
        elif self.state == 'INDEX':
            self.index = self.edit_value(c, self.index)
            self.info(self.row_index, 'index: {0.index:d}'.format(self))
        elif self.state == 'VALUE':
            self.value = self.edit_value(c, self.value)
            self.info(self.row_value, 'value: {0.value:d}'.format(self))

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if (m.group() == 0x01) and (m.type() == 1):
            self.send_primary = self.primary_answer
        super(StCanChannel, self).message_handler(m)

    def exit_handler(self):
        self.run_thread = False

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

def main(channel, primary_size, address):
    import interface
    c = StCanChannel(channel, primary_size=primary_size, address=address)
    i = interface.Interface(c)
    i.run()

if __name__ == '__main__':
    main(0, 1, 1)

