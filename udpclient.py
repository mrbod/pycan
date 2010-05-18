#!/usr/bin/env python
import socket

class UdpClient(socket.socket):
    def __init__(self, peer = None):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM)
        self.peer = peer
        self.connect(self.peer)
        self.setblocking(0)

    def tx(self, str):
        self.send(str)

    def rx(self):
        try:
            return self.recv(4096)
        except:
            return ''

def main():
    import sys
    import getopt
    import time

    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:t:")
    except getopt.GetoptError, e:
        error(e)
        sys.exit(1)

    interval = None
    count = None
    for o in opts:
        if o[0] == '-t':
            interval = float(o[1])
        if o[0] == '-c':
            count = int(o[1])

    ip = None
    port = None

    if len(args) > 0:
        ip = args[0]
    if len(args) > 1:
        port = int(args[1])

    c = UdpClient((ip, port))
    data = sys.stdin.read()
    if data:
        if interval != None:
            if count != None and count > 0:
                while count:
                    c.tx(data)
                    count -= 1
                    time.sleep(interval)
            else:
                while True:
                    c.tx(data)
                    d = c.rx()
                    if d:
                        sys.stdout.write(d)
                        sys.stdout.flush()
                    time.sleep(interval)
        else:
            if count != None and count > 0:
                while count:
                    c.tx(data)
                    count -= 1
            else:
                c.tx(data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
