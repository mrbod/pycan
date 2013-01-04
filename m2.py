#!/usr/bin/env python
import socketcan
import threading
import canmsg

class M2(socketcan.SocketCanChannel):
    def action_handler(self, action):
        if action == 'P':
            ms = [self.msg_class(id=5, data=[x]) for x in range(10)]
            for m in ms:
                self.write(m)
        elif action == 'Q':
            ms = [self.msg_class(id=5, data=[x]) for x in range(100)]
            for m in ms:
                self.write(m)
        elif action == 'T':
            self.run = False
        elif action == 't':
            def foo():
                x = 0
                while self.run:
                    m = self.msg_class(id=5, data=[x & 0xFF])
                    self.write(m)
                    x += 1
            self.run = True
            t = threading.Thread(target=foo)
            t.start()

if __name__ == '__main__':
    import interface
    c = M2()
    i = interface.Interface(c)
    i.run()


