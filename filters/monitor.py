#!/bin/env python
import sys
import threading

OUT = 0
IN = 1
PRIMOUT = 0
PRIMIN = 1
SEC = 2
CFG = 3
MON = 5

def filter(msg):
    if msg.type() == MON:
        sys.stdout.write(chr(msg.data[0]))
        return False
    return True

def send_char(ch, c):
    m = CanMsg()
    m.id = OUT << 9 |  MON
    m.data = [ord(c)]
    ch.write(m)

class MyDict(object):
    def __init__(self):
        pass

    def __getitem__(self, c):
        return lambda ch: send_char(ch, c)

    def get(self, c, dfn):
        return self[c]

action_dict = MyDict()

