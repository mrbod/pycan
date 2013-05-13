#!/usr/bin/env python
import kvaser
import interface
import canmsg
import time
import threading

class Channel(kvaser.KvaserCanChannel):
    def __init__(self, **kwargs):
        super(Channel, self).__init__(**kwargs)
        self.run = False
        self.t = threading.Thread(target=self.foo)

    def close(self):
        self.run = False
        if self.t.is_alive():
            self.t.join()
        super(Channel, self).close()

    def foo(self):
        i = 0
        while self.run:
            m = canmsg.CanMsg()
            m.id = 77
            m.data = [i % 256,1]
            i += 1
            self.write(m)
            time.sleep(0.100)

    def action_handler(self, c):
        if c == 'p':
            m = canmsg.CanMsg()
            m.id = 77
            m.data = [4,3,2,1,1,2,3,4]
            self.write(m)
        elif c == 'P':
            if self.run:
                self.run = False
                self.t.join()
                self.t = threading.Thread(target=self.foo)
            else:
                self.run = True
                self.t.start()
        elif c == 'l':
            for i in range(1000):
                m = canmsg.CanMsg()
                m.id = i << 3
                m.extended = True
                m.data = [4,3,2,1,1,2,3,4]
                self.write(m)
        else:
            super(Channel, self).action_handler(c)

    def message_handler(self, m):
        return super(Channel, self).message_handler(m)

def main():
    try:
        chno = int(sys.argv[1])
    except:
        chno = 0
    ch = Channel(channel=chno)
    try:
        i = interface.Interface(ch)
        i.run()
    finally:
        ch.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

