#!/bin/env python
import bican_master
import canmsg
import sys
import time
import threading
import kvaser

class GDIN(bican_master.StCanMaster):
    def __init__(self, channel=0, address=0):
        bican_master.StCanMaster.__init__(self, channel=channel, primary_size=5, address=address)
        self.primary.data[0] = 0x03
        self.primary.data[2] = 0x40

    def write_text(self, txt, row=0):
        id = (canmsg.GROUP_SEC << 9) | (self.address << 3) | canmsg.TYPE_OUT
        m = canmsg.CanMsg()
        m.can_id = id
        m.data = [0, 25, 0, 64*row, 0, 0]
        self.send(m)
        for i in range(0, len(txt), 2):
            m = canmsg.CanMsg()
            m.can_id = id
            m.data = [0, 25, 0, 127, 0, 0]
            m.data[4] = ord(txt[i])
            try:
                m.data[5] = ord(txt[i + 1])
            except:
                m.data[5] = 0
            self.send(m)

    def action_handler(self, c):
        bican_master.StCanMaster.action_handler(self, c)
        if self.state == 'TEXT':
            if c == '\x1B':
                self.state = 'IDLE'
                self.write_text(self.txt, 1)
            else:
                self.txt = self.txt + c
                print 'txt={0.txt:s}'.format(self)
        elif c == 'k':
            self.state = 'TEXT'
            self.txt = ''

    def message_handler(self, m):
        bican_master.StCanMaster.message_handler(self, m)

    def exit_handler(self):
        bican_master.StCanMaster.exit_handler(self)

if __name__ == '__main__':
    c = GDIN(2, 8)
    bican_master.main(c)

