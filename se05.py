#!/usr/bin/env python
import socketcan
import interface
import canmsg
import stcan
import time

class Msg(canmsg.CanMsg):
    _mfmt = '{0.ssent} {0.sid} {0.time:9.3f} {0.dlc}: {0.data:s}'
    def __str__(self):
        return self._mfmt.format(self)

class Channel(socketcan.SocketCanChannel):
    def __init__(self, channel):
        super(Channel, self).__init__(channel, msg_class=stcan.StCanMsg)
        #super(Channel, self).__init__(channel, msg_class=Msg)
        self.index = -1
        self.limit = False

    def action_handler(self, c):
        if c == 'l':
            self.limit = not self.limit
        elif c == 'p':
            m = Msg()
            m.id = 77
            m.data = [4,3,2,1,1,2,3,4]
            self.write(m)
        elif c == 'P':
            for i in xrange(10):
                m = Msg()
                m.id = 77
                m.data = [i,1,1,1,1,1,1,1]
                self.write(m)
                time.sleep(0.001)
        else:
            self.info(7, c)

    def message_handler(self, m):
        if not self.limit:
            return super(Channel, self).message_handler(m)
        if (m.dlc == 8):
            if not m.sent:
                x = self.index + 1
                if x != m.data[0]:
                    self.info(3, 'missing {0}'.format(x))
                self.index = m.data[0]
            return super(Channel, self).message_handler(m)
        return None

if __name__ == '__main__':
    channel = Channel(0)
    interface = interface.Interface(channel)
    interface.run()

