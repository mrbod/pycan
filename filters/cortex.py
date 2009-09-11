#!/bin/env python
import time
import re
import sys
import os
import signal

TYPE_OUT = 0
TYPE_IN = 1
TYPE_MON = 5
GROUP_PRIMOUT = 0
GROUP_PRIMIN = 1
GROUP_SEC = 2
GROUP_CFG = 3

ADDRESS = 2

SLAVE_PRIMARY = (GROUP_PRIMOUT << 9) | (ADDRESS << 3) | TYPE_OUT
SLAVE_SECONDARY = (GROUP_SEC << 9) | (ADDRESS << 3) | TYPE_OUT
SLAVE_CONFIG = (GROUP_CFG << 9) | (ADDRESS << 3) | TYPE_OUT

monitor_mode = False

txt = ''
primary_reply = 1
def application(msg):
    global txt

    if msg.flags > 7:
        return
    if msg.sent:
        return
    if msg.type() == TYPE_MON:
        if (msg.type() == TYPE_MON) and (msg.group() == GROUP_PRIMIN):
            txt += chr(msg.data[0])
            if (txt[-2:] == '\r\n'):
                print txt[:-2]
                txt = ''
            if (txt[-5:] in ('(Y/N)', 'YMON>', 'CR>):')):
                print txt
                txt = ''
            return
    if msg.group() == GROUP_PRIMIN:
        if primary_reply:
            send_primary(msg.channel)

def format(msg):
    if monitor_mode:
        s = 'M '
    else:
        s = 'N '
    if msg.flags > 7:
        return 'ERROR FRAME %09.3f' % (msg.time / 1000.0,)
    return s + str(msg)

d = 0
m = CanMsg()
def send_primary(ch):
    global d
    m.id = SLAVE_PRIMARY
    m.data = [d]
    d = (d + 1) % 8
    ch.write(m)

def send_secondary(ch):
    m.id = SLAVE_SECONDARY
    m.data = [0, 33, 0, 22, 0xFF, 0xFF]
    ch.write(m)

def send_config(ch):
    m.id = SLAVE_CONFIG
    m.data = [0, 0xCC, 0, 0xCC, 0xCC, 0xCC]
    ch.write(m)

def start_primary(ch):
    global primary_reply
    primary_reply = not primary_reply

class MyDict(object):
    def __init__(self):
        self.cmd = {
                'c':lambda ch: send_config(ch),
                's':lambda ch: send_secondary(ch),
                'p':lambda ch: start_primary(ch),
                'P':lambda ch: send_primary(ch),
                }

    def monitor(self, ch, c):
        m = CanMsg()
        m.id = (GROUP_PRIMOUT << 9) |  TYPE_MON
        m.data = [ord(c)]
        ch.write(m)

    def foo(self, ch, c):
        pass

    def __getitem__(self, c):
        global monitor_mode
        if ord(c) == 0x1B:
            monitor_mode = not monitor_mode
            return lambda ch: self.foo(ch, c)
        if monitor_mode:
            return lambda ch: self.monitor(ch, c)
        return self.cmd[c]

    def get(self, c, dfn):
        try:
            return self[c]
        except:
            return dfn

actions = MyDict()

def handler(m):
    if monitor_mode:
        pass
    else:
        print format(m)
    application(m)

