#!/bin/env python
import time

OUT = 0
IN = 1
SEC = 2
CFG = 3

# secondary data
VOLTAGE = 22
SPEED_A = 27
READ_UART1 = 31
WRITE_UART1 = 32
SUM_FREQ = 51
INPUT_LIGHT = 54
SWITCH = 55
V48 = 56
EEPROM = 100

SEC_REQ = 99

#config data
NODE_TYPE = 30
VERSION = 31
ART_NO = 32
SERIAL_NO = 33

CFG_REQ = 99

sec_index = {SUM_FREQ:'SUM_FREQ', EEPROM:'EEPROM', SEC_REQ:'SEC_REQ', VOLTAGE:'VOLTAGE', SPEED_A:'SPEED_A', READ_UART1:'READ_UART1', WRITE_UART1:'WRITE_UART1', INPUT_LIGHT:'INPUT_LIGHT', SWITCH:'SWITCH', V48:'V48'}

cfg_index = {NODE_TYPE:'NODE_TYPE', VERSION:'VERSION', ART_NO:'ART_NO', SERIAL_NO:'SERIAL_NO'}

def bin(byte):
    return ''.join([str((byte >> i) & 0x01) for i in range(8)])

def prim_tx(m):
    return '%s %s' % (bin(m.msg[0]), bin(m.msg[1]))

def prim_rx(m):
    return '%s %s %s' % (bin(m.msg[0]), bin(m.msg[1]), bin(m.msg[2]))

def mychr(d):
    s = chr(d)
    if s.isalnum():
        return s
    else:
        return '.'

def sec_tx(m):
    try:
        index = (m.msg[0] << 8) + m.msg[1]
        if index == SEC_REQ:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %s' % (sec_index[index], sec_index[val])
        elif index in (VOLTAGE, V48):
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %.1fV' % (sec_index[index], val / 10.0)
        elif index in (READ_UART1, WRITE_UART1):
            s = "'%s'" % ''.join([mychr(c) for c in m.msg[2:]])
            d = '[%s]' % ', '.join([('%02X' % c) for c in m.msg[2:]])
            return '%s %s %s' % (sec_index[index], s, d)
        elif index == SPEED_A:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %3.2f km/h' % (sec_index[index], val / 256.0)
        elif index == SUM_FREQ:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %d Hz' % (sec_index[index], val)
        else:
            vals = [((m.msg[i] << 8) + m.msg[i + 1]) for i in range(m.dlc() - 2)]
            s = ', '.join([('0x%04X' % x) for x in vals])
            return '%s %s' % (sec_index[index], s)
    except Exception, e:
        print '*', e
        print '*', m
        raise

sec_rx = sec_tx

def cfg_tx(m):
    index = (m.msg[0] << 8) + m.msg[1]
    val = (m.msg[2] << 8) + m.msg[3]
    if index == CFG_REQ:
        return '%s %s' % (cfg_index[index], cfg_index[val])
    else:
        return '%s %s' % (cfg_index[index], val)

cfg_rx = cfg_tx

def fmt(m):
    try:
        if m.addr() == 2:
            if m.group() == CFG:
                return 'lcd data'
            else:
                return 'lcd command'
        if m.group() == OUT:
            return prim_tx(m)
        if m.group() == IN:
            return prim_rx(m)
        if m.group() == SEC:
            if m.type() == OUT:
                return sec_tx(m)
            else:
                return sec_rx(m)
        if m.group() == CFG:
            if m.type() == OUT:
                return cfg_tx(m)
            else:
                return cfg_rx(m)
    except:
        return 'unknown'

old_out = [-1, -1]
old_in = [-1, -1, -1]
old_out_time = time.time()
old_in_time = time.time()
use_time = False

cnt = 0

def filter(msg):
    global cnt
    global old_in_time
    global old_out_time
    try:
        cnt += 1
        if msg.addr() == 2:
            return True
        if msg.group() == OUT:
            res = False
            if use_time and ((time.time() - old_out_time) > 5.0):
                old_out_time = time.time()
                res = True
            elif msg.msg[0] != old_out[0]:
                res = True
            elif msg.msg[1] != old_out[1]:
                res = True
            if res:
                old_out[0] = msg.msg[0]
                old_out[1] = msg.msg[1]
            return res
        if msg.group() == IN:
            res = False
            if use_time and ((time.time() - old_in_time) > 5.0):
                old_in_time = time.time()
                res = True
            elif msg.msg[0] != old_in[0]:
                res = True
            elif msg.msg[1] != old_in[1]:
                res = True
            elif msg.msg[2] != old_in[2]:
                res = True
            if res:
                old_in[0] = msg.msg[0]
                old_in[1] = msg.msg[1]
                old_in[2] = msg.msg[2]
            return res
        return True
    except:
        return True

def format(msg):
    m = ', '.join(['%02X' % x for x in msg.msg])
    t = msg.time / 1000.0
    st = msg.stcan()
    return '%06d %08.3f (%03X:%s) [%s]: %s' % (cnt, t, msg.id, st, m, fmt(msg))

def parse_uart():
    import sys
    import re
    r  = re.compile(r'(\d+)\s(\S+)\s\([^\)]+\)\s[^:]+: (READ|WRITE)_UART1\s+\'[^\']*\'\s+\[(.+)\]')
    for l in sys.stdin:
        o = r.match(l)
        if o:
            print o.groups()

def main():
    parse_uart()

if __name__ == '__main__':
    main()
