#!/usr/bin/env python
import sys

for L in sys.stdin:
    d = L.split()
    if len(d) > 0:
        if d[0] == '0':
            id = int(d[4], 16)
            group = id >> 9
            typ = id & 0x07
            address = (id >> 3) & 0x3F
            D = [str(z) for z in [group, address, typ]] + d
            print chr(0x09).join(D)

