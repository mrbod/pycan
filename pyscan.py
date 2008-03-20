#!/usr/bin/env python
from pycan import CanChannel

def fmt(msg):
    return str(msg)

if __name__ == '__main__':
    import sys
    import time
    import getopt

    filterfile = None
    filter_func = None
    format_func = fmt
    bitrate = 125
    channel = 0
    address = []
    group = []
    types = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:b:a:g:t:f:")
    except getopt.GetoptError, e:
        print 'Usage: %s [-c <channel>] [-b <bitrate>]' % (sys.argv[0],)
        print '\t-c channel, default %d' % channel
        print '\t-b bitrate, default %d' % bitrate
        print '\t-f filter, load file as filter'
        print '\t-a address to show, can be repeated'
        print '\t-g group to show, can be repeated'
        print '\t-t type to show, can be repeated'
        print
        print >>sys.stderr, e
        sys.exit(1)

    for o in opts:
        if o[0] == '-c':
            channel = int(o[1])
        elif o[0] == '-b':
            bitrate = int(o[1])
        elif o[0] == '-a':
            address.append(int(o[1]))
        elif o[0] == '-g':
            group.append(int(o[1]))
        elif o[0] == '-t':
            types.append(int(o[1]))
        elif o[0] == '-f':
            filterfile = o[1]

    if filterfile:
        try:
            s = 'import %s as filter' % filterfile
            exec s
            try:
                filter_func = filter.filter
            except AttributeError, e:
                print >>sys.stderr, 'Using standard filter'
            try:
                format_func = filter.format
            except AttributeError, e:
                print >>sys.stderr, 'Using standard format'
        except ImportError:
            print >>sys.stderr, 'Unable to import filter file %s' % filterfile
            sys.exit(1)

    try:
        ch = CanChannel(channel, bitrate)
        while True:
            m = ch.read()
            if m:
                if group and not (m.group() in group):
                    continue
                if address and not (m.addr() in address):
                    continue
                if types and not (m.type() in types):
                    continue
                if filter_func and not filter_func(m):
                    continue
                print format_func(m)
            else:
                sys.stdout.flush()
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
