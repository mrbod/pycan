#!/usr/bin/env python
import sys
import canmsg

def parse(cols):
    date = [int(x) for x in cols[0].split('-')]
    t, us = cols[1][-1].split('.')
    date = [.split(':')]
    m = canmsg.CanMsg()
    m.time = time.mktime(
    m.sent = cols[3] == 'S'
    m.channel = int(cols[4])
    if len(cols[5]) > 3:
        m.extended = True
    else:
        m.extended = False
    m.id = int(cols[5], 16)
    m.data = [int(x, 16) for x in cols[-1][1:-1].split(', ')]
    return m

def main(f):
    canmsg.format_set(canmsg.FORMAT_STCAN)
    cnt = 0
    for L in f:
        cols = L.strip().split(None, 8)
        if (len(cols) == 9) and (cols[2] == 'serial'):
            print cnt, ':', parse(cols)
            cnt += 1

if __name__ == '__main__':
    try:
        main(sys.stdin)
    except KeyboardInterrupt:
        pass

