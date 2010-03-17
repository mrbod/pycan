#!/bin/env python
import canmsg
import sys
import time
import threading
import kvaser

class StCanMaster(kvaser.KvaserCanChannel):
    def __init__(self, channel=0, primary_size=0, address=0):
        self.message_queue = []
        self.state = 'IDLE'
        self.action_handler_T = time.time()
        self.address = address
        self.index = 0
        self.value = 0
        self.primary_answer = False
        self.send_primary = False
        id = (self.address << 3)
        self.primary = canmsg.CanMsg(id=id, data=primary_size*[0])
        self.exception = None
        self.thread = threading.Thread(target=self.run)
        self.run_thread = True
        self.thread.start()
        kvaser.KvaserCanChannel.__init__(self, silent=False, channel=channel, bitrate=kvaser.canBITRATE_125K)

    def run(self):
        try:
            while self.run_thread:
                if self.send_primary:
                    self.send_primary = False
                    self.write(self.primary)
                if time.time() - self.action_handler_T > 5.0:
                    self.state = 'IDLE'
                if len(self.message_queue) > 0:
                    m = self.message_queue.pop(0)
                    self.write(m)

        except Exception, e:
            self.exception = e
            raise

    def send(self, m):
        self.message_queue.append(m)

    def action_handler(self, c):
        self.action_handler_T = time.time()
        if self.state == 'IDLE':
            if c == 'p':
                self.send_primary = True
            elif c == 'P':
                self.primary_answer = not self.primary_answer
            elif c == 'i':
                self.index = 0
                self.state = 'INDEX'
            elif c == 'v':
                self.value = 0
                self.state = 'VALUE'
            elif c == 't':
                self.toggle_index = 0
                self.state = 'TOGGLE'
        elif self.state == 'INDEX':
            if c in '0123456789':
                self.index = self.index * 10 + int(c)
                print 'index={0.index:d}'.format(self)
            else:
                self.state = 'IDLE'
        elif self.state == 'VALUE':
            if c in '0123456789':
                self.value = self.value * 10 + int(c)
                print 'value={0.value:d}'.format(self)
            else:
                self.state = 'IDLE'
        elif self.state == 'TOGGLE':
            if c in '0123456789':
                self.toggle_index = self.toggle_index * 10 + int(c)
                print 'toggle bit index={0.toggle_index:d}'.format(self)
            else:
                B = self.toggle_index / 8
                b = self.toggle_index % 8
                mask = 1 << b
                if B < self.primary.dlc():
                    d = self.primary.data[B]
                    if d & mask:
                        d = d & ~mask
                        print 'bit {0.toggle_index:d}=0'.format(self)
                    else:
                        d = d | mask
                        print 'bit {0.toggle_index:d}=1'.format(self)
                    self.primary.data[B] = d
                else:
                    print 'Value out of range', self.toggle_index
                self.state = 'IDLE'

    def message_handler(self, m):
        if self.exception:
            raise self.exception
        if (m.group() == 0x01) and (m.type() == 1):
            self.send_primary = self.primary_answer
        print m

    def exit_handler(self):
        self.run_thread = False

    def debug(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

def main(channel):
    try:
        channel.open()
        kvaser.main(channel)
    finally:
        channel.exit_handler()

if __name__ == '__main__':
    c = StCanMaster(2, silent=silent)
    main(c)

