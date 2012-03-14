#!/usr/bin/env python
import sys
import socketcan
import canmsg
import stcan
import optparse
import random
import time

def random_data():
    dlc = random.randint(0, 8)
    return [random.randint(0, 255) for x in xrange(dlc)]

def main(cnt, canid=None, data=None, file=None):
    if file == None:
        ch = socketcan.SocketCanChannel()
        ch.open()
    id = canid
    if data != None:
        data = data.strip()
        if len(data) > 0:
            d = [int(s, 0) for s in data.split(',')[0:8]]
        else:
            d = []
    for i in xrange(cnt):
        if data == None:
            d = random_data()
        if id == None:
            canid = random.randint(0, 2047)
        m = cls(id=canid, data=d)
        if file == None:
            ch.write(m)
        else:
            m.time = time.time()
            file.write(str(m))
            file.write('\n')

if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('-c', '--count', dest='count', type='int', default=1,
            help='message COUNT', metavar='COUNT')
    p.add_option('-i', '--canid', dest='canid', type='int', default=None,
            help='message id', metavar='CANID')
    p.add_option('-d', '--data', dest='data', type='string', default=None,
            help='message data, i.e. 34,0x4,0x35,123. No space allowed.', metavar='DATA')
    p.add_option('-s', '--stdout', dest='stdout', action='store_true', default=False,
            help='dump messages on stdout')
    p.add_option('-b', '--bican', dest='bican', action='store_true', default=False,
            help='dump messages on stdout')
    (opts, args) = p.parse_args()
    if len(args) > 0:
        sys.stderr.write('Error: unknown arguments, {0}\n\n'.format(str(args)))
        p.print_usage()
        sys.exit(1)
    f = None
    if opts.stdout:
        f = sys.stdout
    cls = canmsg.CanMsg
    if opts.bican:
        cls = stcan.StCanMsg
    try:
        main(opts.count, opts.canid, opts.data, f)
    except KeyboardInterrupt:
        pass

