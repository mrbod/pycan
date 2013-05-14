#!/usr/bin/env python
import sys
import time
import canmsg
import biscan
import matplotlib.pyplot as plt
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

def mgen():
    for m in biscan.convert(sys.stdin):
        if m.id in (0x010, 0x211):
            yield m

def bah():
    import matplotlib.animation as ani
    actual_pos = 0x211
    set_pos = 0x010
    sync = 0x000
    labels = {sync: 'sync message',
            set_pos: 'set position',
            actual_pos: 'actual position'}
    fig = plt.figure()
    line, = plt.plot([], [], 'o-')
    ax = plt.subplot(111)
    setl, = plt.plot([], [])
    actl, = plt.plot([], [])
    synl, = plt.plot([], [])
    def anim(m):
        if m.id == actual_pos:
            actl.set_xdata(np.append(actl.get_xdata(), m.time))
            actl.set_ydata(np.append(actl.get_ydata(), qlpos(m)))
            return actl
        elif m.id == set_pos:
            setl.set_xdata(np.append(setl.get_xdata(), m.time))
            setl.set_ydata(np.append(setl.get_ydata(), qlpos(m)))
            return setl
    a = ani.FuncAnimation(fig, anim, mgen)
    plt.show()

def main():
    actual_pos = 0x211
    set_pos = 0x010
    sync = 0x000
    labels = {sync: 'sync message',
            set_pos: 'set position',
            actual_pos: 'actual position'}
    idm = {}
    pos = {}
    # convert
    for m in biscan.convert(sys.stdin):
        l = idm.setdefault(m.id, [])
        l.append(m)
    # extract positions
    for id in (set_pos, actual_pos):
        pos[id] = np.array([np.array((m.time, qlpos(m))) for m in idm[id]]).transpose()
    # sync time
    synt = np.array([m.time for m in idm[sync]]).transpose()
    # position sync markers on position lines
    syns = np.interp(synt, pos[set_pos][0], pos[set_pos][1])
    syna = np.interp(synt, pos[actual_pos][0], pos[actual_pos][1])
    # start the plot
    ax = plt.subplot(111)
    # sync markers
    plt.plot(synt, syns, 'o', label=labels[sync], markersize=5.0)
    plt.plot(synt, syna, 'o', label=labels[sync], markersize=5.0)
    # positions
    for id in (set_pos, actual_pos):
        time, position = pos[id]
        plt.plot(time, position, 'x-', label=labels[id], markersize=5.0)
    # all about looks
    plt.xlabel('Time [s]')
    plt.ylabel('Position [pulses]')
    plt.grid()
    plt.legend()
    plt.show()

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
