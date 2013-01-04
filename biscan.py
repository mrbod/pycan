#!/usr/bin/env python
import sys
import canmsg

canmsg.format_set(canmsg.FORMAT_STCAN)

cnt = 0

def convert(f):
    for L in sys.stdin:
        try:
            m = canmsg.CanMsg.from_biscan(L)
            yield m
        except Exception, e:
            sys.stderr.write(str(e) + '\n')

def calc_load(messages):
    fmt = '{0:8.3f} '
    for i, m in enumerate(messages):
        f = []
        if i >= 1:
            f.append(1 / (m.time - messages[i - 1].time))
        else:
            f.append(0.0)
        if i >= 3:
            f.append(3 / (m.time - messages[i - 3].time))
        else:
            f.append(0.0)
        if i >= 7:
            f.append(7 / (m.time - messages[i - 7].time))
        else:
            f.append(0.0)
        if i >= 17:
            f.append(17 / (m.time - messages[i - 17].time))
        else:
            f.append(0.0)
        if i >= 91:
            f.append(91 / (m.time - messages[i - 91].time))
        else:
            f.append(0.0)
        for v in f:
            sys.stdout.write(fmt.format(v))
        sys.stdout.write(str(m))
        sys.stdout.write('\n')

def output(messages):
    for m in messages:
        print(m)

def main():
    load = False
    for a in sys.argv[1:]:
        if a == 'load':
            load = True
    d = [m for m in convert(sys.stdin)]
    if load:
        calc_load(d)
    else:
        output(d)


if __name__ == '__main__':
    main()

