#!/usr/bin/env python
import sys
import time
import canmsg
import biscan
import matplotlib as mpl
import matplotlib.pyplot as pp
import numpy as np

canmsg.format_set(canmsg.FORMAT_STCAN)

def convert(f):
    for L in sys.stdin:
        try:
            m = canmsg.CanMsg.from_biscan(L)
            yield m
        except Exception, e:
            sys.stderr.write(str(e) + '\n')

def qlpos(m):
    p = m.data[2]
    p = (p << 8) + m.data[3]
    p = (p << 8) + m.data[4]
    p = (p << 8) + m.data[5]
    return p

def main():
    idm = {}
    pos = {}
    for m in biscan.convert(sys.stdin):
        l = idm.setdefault(m.id, [])
        l.append(m)
    for id in (0x010, 0x211):
        pos[id] = np.array([np.array((m.time, qlpos(m))) for m in idm[id]]).transpose()
        pp.plot(pos[id])
    pp.show()
    print pos

def foo():
    d = [m for m in biscan.convert(sys.stdin)]
    mt = {}
    mp = {}
    for m in d:
        dT = m.time - mt.get(m.id, 0)
        print '{0:.6f}'.format(dT),
        mt[m.id] = m.time
        if abs(0.005 - dT) > 0.001:
            print '*',
        else:
            print ' ',
        if m.id in (0x10, 0x211):
            p = qlpos(m)
            dP = p - mp.get(m.id, 0)
            mp[m.id] = p
            print '{0:5d} {1:9d}'.format(dP, p),
        else:
            print 15 * ' ',
        print m

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

