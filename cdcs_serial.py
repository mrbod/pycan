#!/usr/bin/env python
import sys
import re
import canmsg

pattern =  r'(\S*)\s(\S*): (serial) ([RS])\s+'
pattern +=  r'(\d+)\s+'
pattern += r'([a-fA-F0-9]+)\s+'
pattern += r'(\d+)\s+'
pattern += r'(\d+)\s+'
pattern += r'\[([^]]+)\]'
r = re.compile(pattern)

def parse(cols):
    #date = [int(x) for x in cols[0].split('-')]
    #t = [float(x) for x in cols[1][:-1].split(':')]
    #T = t[0] * 60 * 60 + t[1] * 60 + t[2]
    #t = '{0:8.3f}'.format(T)
    t = cols[0] + ' ' + cols[1] + ':'
    m = canmsg.CanMsg()
    m.sent = cols[3] == 'S'
    if m.sent:
        m.time = long(cols[7]) / 10e6
    else:
        m.time = (long(cols[7]) & 0x00FFFFFF) / 10e6
    m.channel = int(cols[4])
    if len(cols[5]) > 3:
        m.extended = True
    else:
        m.extended = False
    m.can_id = int(cols[5], 16)
    m.data = [int(x, 16) for x in cols[-1].split(', ')]
    return t, cols[3], cols[4], m

def main(f):
    canmsg.format_set(canmsg.FORMAT_STCAN)
    cnt = 0
    for l in f:
        o = r.match(l)
        if o:
            grps = o.groups()
            if len(grps) == 9:
                for x in parse(o.groups()):
                    print x,
                print
            cnt += 1

if __name__ == '__main__':
    try:
        main(sys.stdin)
    except KeyboardInterrupt:
        pass

