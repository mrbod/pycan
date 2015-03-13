#!/usr/bin/env python
import sys
from pycan import canmsg

canmsg.format_set(canmsg.FORMAT_BICAN)

def convert(f):
    for L in sys.stdin:
        try:
            m = canmsg.CanMsg.from_biscan(L)
            yield m
        except Exception as e:
            sys.stderr.write(str(e) + '\n')

def main():
    try:
        for m in convert(sys.stdin):
            print(m)
    except KeyboardInterrupt:
        pass

