#!/usr/bin/env python
import sys
import canmsg

canmsg.format_set(canmsg.FORMAT_STCAN)

m = canmsg.CanMsg()

def conv(line):
    data = line.strip().split(None, 7)
    m.can_id = int(data[5], 16)
    m.time = int(data[4]) / 1000.0
    m.data = [int(x, 16) for x in data[-1].split()]
    print m

for l in sys.stdin:
    try:
        conv(l)
    except ValueError:
        print l.strip()
