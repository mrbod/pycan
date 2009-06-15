#!/bin/env python
import time
import re
import sys
import os
import signal
import threading

OUT = 0
IN = 1
MON = 5
PRIMOUT = 0
PRIMIN = 1
SEC = 2
CFG = 3

address = 2

def bin(byte):
    return ''.join([str((byte >> i) & 0x01) for i in range(8)])

def eq_data(a, b):
    if (a == None) or (b == None):
        return False
    if len(a.msg) != len(b.msg):
        return False
    for ab, bb in zip(a.msg, b.msg):
        if ab != bb:
            return False
    return True

def vconv(x):
    return 40.0 / 1032 * x

config_index = 100
config_data = 0
old_prim = None
flags = False
def filter(msg):
    global old_prim
    global flags
    global config_data
    if msg.flags > 7:
        if not flags:
            flags = True
            return True
        return False
    else:
        flags = False
    if msg.addr() == address:
        if msg.group() == PRIMIN:
            return True
            if eq_data(old_prim, msg):
                return False
            old_prim = msg
        elif msg.group() == SEC:
            index = msg.msg[1]
            if index == 42:
                #ambient light
                m = CanMsg(id=(SEC << 9) | (msg.addr() << 3) | OUT, msg=[0, 43, 0, msg.msg[3]])
                msg.channel.write(m)
                print m
                m.msg[1] = 44
                msg.channel.write(m)
                print m
        return True
    else:
        if msg.group() == PRIMIN:
            m = CanMsg()
            m.id = (PRIMOUT << 9) | (msg.addr() << 3) | OUT
            m.msg = msg.msg[:]
            msg.channel.write(m)
            print m
            return True
            m.id = (CFG << 9) | (msg.addr() << 3) | OUT
            m.msg = [0, 99, 0, config_index]
            msg.channel.write(m)
            print m
        elif msg.group() == CFG:
            index = msg.msg[1]
            if index == config_index:
                #config_data = 5
                config_data = (msg.msg[2] << 8) + msg.msg[3]
                m = CanMsg()
                m.id = (CFG << 9) | (msg.addr() << 3) | OUT
                m.msg = [0, config_index, (config_data >> 8) & 0xFF, config_data & 0xFF]
                msg.channel.write(m)
        return True

def fmt_values(v):
    v = [(a << 8) + b for a,b in zip(v[0::2], v[1::2])]
    v = ['%d(0x%X)' % (a, a) for a in v]
    return ', '.join(v)

def format(msg):
    if msg.group() == SEC:
        if msg.type() == IN:
            index = msg.msg[1]
            print msg
            return 'SEC INDEX(%d): %s' % (index, fmt_values(msg.msg[2:]))
    if msg.group() == CFG:
        if msg.type() == IN:
            index = msg.msg[1]
            print msg
            return 'CFG INDEX(%d): %s' % (index, fmt_values(msg.msg[2:]))
    return str(msg)

address = 2

class BThread(threading.Thread):
    def __init__(self, channel):
        threading.Thread.__init__(self)
        self.KeepAlive = True
        self.channel = channel
        self.byteno = None
        self.bitno = None

    def run(self):
        m = CanMsg()
        m.id = (PRIMOUT << 9) | (address << 3) | OUT
        m.msg = [3, 0, 0x40, 0, 0]
        om = m
        Tprimary = time.time()
        Tamb = Tprimary
        while self.KeepAlive:
            try:
                T = time.time()
                if (T - Tprimary) > 0.4:
                    Tprimary = T
                    self.__toggle_bit(m)
                    self.channel.write(m)
                    print m
                #if (T - Tamb) > 1.0:
                    #Tamb = T
                    #send_secondary(self.channel, 0x63, 42)
                time.sleep(0.1)
            except Exception, e:
                print 'thread:', e

    def __toggle_bit(self, m):
        if self.bitno != None:
            byte = self.bitno / 8
            bit = self.bitno % 8
            mask = (1 << bit)
            val = m.msg[byte]
            if val & mask:
                val = val & (0xFF & ~mask)
                b = 0
            else:
                val = val | mask
                b = 1
            m.msg[byte] = val
            print 'toggle_bit(%d) -> %d' % (self.bitno, b)
            self.bitno = None

    def toggle_bit(self, bitno):
        self.bitno = bitno

thread = None
def primary(ch):
    global thread
    if thread != None:
        thread.KeepAlive = False
        thread = None
    else:
        thread = BThread(ch)
        thread.start()

index = 22
value = 0
config = CanMsg()
config.id = (CFG << 9) | (address << 3) | OUT
config.msg = []

def inc_index_1(ch):
    global index
    index += 1
    print 'index=%d' % index

def dec_index_1(ch):
    global index
    index -= 1
    print 'index=%d' % index

def inc_index_10(ch):
    global index
    index += 10
    print 'index=%d' % index

def dec_index_10(ch):
    global index
    index -= 10
    print 'index=%d' % index

def inc_value_1(ch):
    global value
    value += 1
    print 'value=%d' % value

def dec_value_1(ch):
    global value
    value -= 1
    print 'value=%d' % value

def inc_value_10(ch):
    global value
    value += 10
    print 'value=%d' % value

def dec_value_10(ch):
    global value
    value -= 10
    print 'value=%d' % value

def inc_value_100(ch):
    global value
    value += 100
    print 'value=%d' % value

def dec_value_100(ch):
    global value
    value -= 100
    print 'value=%d' % value

secondary = CanMsg()
secondary.id = (SEC << 9) | (address << 3) | OUT
def send_secondary(ch, i, val):
    secondary.msg = [0, i, (val >> 8) & 0xFF, val & 0xFF]
    ch.write(secondary)
    print secondary

config = CanMsg()
config.id = (CFG << 9) | (address << 3) | OUT
def send_config(ch, i, val):
    config.msg = [0, i, (val >> 8) & 0xFF, val & 0xFF]
    ch.write(config)
    print config

def toggle_bit(ch):
    if thread and thread.KeepAlive:
        thread.toggle_bit(index)
    else:
        print 'toggle_bit: thread dead'

def number_2_disp(ch):
    m = CanMsg()
    m.id = secondary.id
    m.msg = [0, 26, ((index & 0x7) << 5) | ((index & 0x3) << 3), 0, (value >> 8) & 0xFF, value & 0xFF]
    ch.write(m)
    print m

def text_2_disp(ch):
    m = CanMsg()
    m.id = secondary.id
    m.msg = [0, 25, 0x80, 0x44, ord('R'), ord('D')]
    ch.write(m)
    print m

def clear_screen(ch):
    m = CanMsg()
    m.id = secondary.id
    m.msg = [0, 25, 0x40, 0, ord('R'), ord('D')]
    ch.write(m)
    print m

def show_on_display(ch):
    m = CanMsg()
    m.id = secondary.id
    s = 'antal6'
    m.msg = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    print m

def show_on_display2(ch):
    m = CanMsg()
    m.id = secondary.id
    s = '$ES\0'
    m.msg = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    s = '$LC1,5'
    m.msg = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    s = 'BArnEY'
    m.msg = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    print m

action_dict = {
        'p':primary,
        's':lambda ch: send_secondary(ch, index, value),
        'S':lambda ch: send_secondary(ch, 0x63, index),
        'c':lambda ch: send_config(ch, index, value),
        'C':lambda ch: send_config(ch, 0x63, index),
        'i':inc_index_1,
        'I':dec_index_1,
        'o':inc_index_10,
        'O':dec_index_10,
        'v':inc_value_1,
        'V':dec_value_1,
        'b':inc_value_10,
        'B':dec_value_10,
        'n':inc_value_100,
        'N':dec_value_100,
        't':toggle_bit,
        'k':number_2_disp,
        'K':text_2_disp,
        'd':show_on_display,
        'D':show_on_display2,
        }

def exit():
    if thread != None:
        thread.KeepAlive = False

