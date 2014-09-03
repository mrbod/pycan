#!/usr/bin/env python
import sys
import os
import os.path
import glob
import re
import canmsg

os.stat_float_times(True)

canmsg.format_set(canmsg.FORMAT_BICAN)

pattern =  r'(\S*)\s(\S*): (serial) ([RS])\s+'
pattern += r'(\d+)\s+'
pattern += r'([a-fA-F0-9]+)\s+'
pattern += r'(\d+)\s+'
pattern += r'(\d+)\s+'
pattern += r'\[([^]]+)\]'
r = re.compile(pattern)

def out(s):
    sys.stdout.write(s)

def outerr(s):
    sys.stderr.write(s)

class File(object):
    def __init__(self, filename):
        self.name = filename
        self.mtime = os.stat(filename).st_mtime

    def __str__(self):
        return self.name

class Foo(object):
    def __init__(self):
        self.msgs = []
        self.parse = None
        self.ids = {}

    def search(self, pattern):
        fl = map(File, filter(os.path.isfile, glob.glob(pattern)))
        fl.sort(key=lambda x: x.mtime)
        return fl

    def status(self, s):
        cnt = len(self.msgs)
        if (cnt % 2347) == 0:
            out('\rprocessing {0} {1:10d} messages'.format(s, cnt))
            sys.stdout.flush()

    def operate(self, f):
        start = len(self.msgs)
        for l in open(f.name):
            m = self.parse(l)
            if m:
                self.msgs.append(m)
                if m.can_id not in self.ids:
                    self.ids[m.can_id] = []
                self.ids[m.can_id].append(m)
                self.status(str(f))
        s = '\r{0} has {1} messages                                \n'
        out(s.format(str(f), len(self.msgs) - start))

    def __call__(self, parser, pattern='', callback=None, limit=None):
        self.parse = parser
        files = self.search(pattern)
        if limit and (limit > 1):
            out('{1} of {0} files to process\n'.format(len(files), limit))
            files = files[-limit:]
        else:
            out('{0} files to process\n'.format(len(files)))
        for i, f in enumerate(files):
            if limit and (limit <= i):
                break
            self.operate(f)
        out('a total of {0} messages processed\n'.format(len(self.msgs)))
        for k, v in self.ids.items():
            out('{0}: {1} messages\n'.format(v[0].bican, len(v)))

def parse(line):
    o = r.match(line)
    if not o:
        return None
    cols = o.groups()
    if len(cols) != 9:
        return None
    t = [float(x) for x in cols[1][:-1].split(':')]
    T = t[0] * 60 * 60 + t[1] * 60 + t[2]
    tstr = '{0:8.3f}'.format(T)
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
    return m

def main(pattern, limit):
    foo = Foo()
    foo(parse, pattern=pattern, limit=limit)

if __name__ == '__main__':
    try:
        pattern = 'cdcs.log*'
        limit = 1
        for a in sys.argv[1:]:
            if a.startswith('-'):
                try:
                    limit = int(a[1:], 0)
                except:
                    outerr('unknown argument: <{0}>\n'.format(a))
                    sys.exit(1)
            else:
                pattern = a
                break
        main(pattern, limit)
    except KeyboardInterrupt:
        pass
