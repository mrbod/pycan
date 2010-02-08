#!/bin/env python
import sys
import re
import canmsg

def dump(msg, lineno=0):
    id = (msg[0] << 8) | msg[1]
    data = msg[2:]
    cm = canmsg.CanMsg(id, data)
    sys.stdout.write('L%d %s\n' % (lineno, str(cm)))
    sys.stdout.flush()

def parse_msg(msg):
    # split msg in bytes and convert to integer
    try:
        res = [int('0x' + b, 16) for b in msg.strip().split(' ')]
    except:
        s = 'parse_msg: failed on <%s>\n' % msg
        sys.stderr.write(s)
        raise
    return res

extre = re.compile(r' 10 03')

def process(data):
    r = extre.split(data)
    if len(r) >= 2:
        for m in r[0:-1]:
            try:
                dump(parse_msg(r[0]), lineno)
            except:
                s = 'main: failed on <%s>\n' % data
                sys.stderr.write(s)
                raise
        return r[-1]
    sys.stderr.write('INCOMPLETE: <%s>\n' % data)
    return data

def main(f):
    datare = re.compile(r'([0-9]+).*\bLength\s+[0-9]+:((\s[0-9a-zA-Z]{2})+)')
    data = ['', '']
    WRITE = 0
    READ = 1
    # find data lines in input
    for line in f:
        ro = datare.match(line)
        if ro:
            lineno = int(ro.group(1))
            bytes = ro.group(2).replace(' 10 10', ' 10')
            what = 0
            if writere.search(line):
            what = 0
                data[WRITE] += bytes
                data[WRITE] = process(data[WRITE])
            else:
            what = 0
                data[READ] += bytes
                d = data[READ]

if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = file(sys.argv[1])
    else:
        f = sys.stdin
    main(f)
