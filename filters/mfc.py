#!/bin/env python
import time
import re
import canmsg
import sys

OUT = 0
IN = 1
SEC = 2
CFG = 3

# secondary data
XA11 = 18
VOLTAGE_INT = 22
THERMO = 23
VOLTAGE_EXT = 24
SPEED_A = 27
FRONTBOX_VOLTAGE = 31
READ_UART1 = 31
SEND_UART1 = 32
HYDRAULIC_PRESSURE = 40
A48V_REAR = 41
YZ_POS = 50
SUMMER_FREQUENCY = 51
SPEED_B = 52
SPEED_C = 53
INPUT_LIGHT = 54
SWITCH = 55
A48V_FRONT = 56
LEFT_LOCK_PIN_CURRENT = 57
RIGHT_LOCK_PIN_CURRENT = 58
TRAILER_INFO_RESISTANCE = 59
ERROR_INFO = 60
DISTANCE_INFO = 61
NO_OF_COUPLINGS_INFO = 62
LOGG = 65
MANUAL_OUTPUT = 70
SEMI_AUTOMATIC_STEPPING = 71
CYCLE_TIME = 80
EEPROM = 100
SEC_REQ = 99

#config data
RANGE_24V_FRONT = 10
RANGE_24V_REAR = 11
RANGE_48V_FRONT = 12
RANGE_48V_REAR = 13
RANGE_CURR_LEFT_PIN = 14
RANGE_CURR_RIGHT_PIN = 15
COUPLING_VARIANT = 20
NODE_TYPE = 30
VERSION = 31
ART_NO = 32
SERIAL_NO = 33
PULLUP_PULLDOWN = 47         
CLEAR_EEPROM = 50
VOLTAGE_WINDOW = 72
VOLTAGE_FACTOR = 73
TEMP_VALUE_MODE = 74
SPEED_FACTOR = 80
XA13_FACTOR = 81
MANOUVER_MODE = 90

CFG_REQ = 99

sec_index = {XA11:'XA11', VOLTAGE_INT:'VOLTAGE_INT', VOLTAGE_EXT:'VOLTAGE_EXT', THERMO:'THERMO', SPEED_A:'SPEED_A', FRONTBOX_VOLTAGE:'FRONTBOX_VOLTAGE', READ_UART1:'READ_UART1', SEND_UART1:'SEND_UART1', HYDRAULIC_PRESSURE:'HYDRAULIC_PRESSURE', A48V_REAR:'A48V_REAR', YZ_POS:'YZ_POS', SUMMER_FREQUENCY:'SUMMER_FREQUENCY', SPEED_B:'SPEED_B', SPEED_C:'SPEED_C', INPUT_LIGHT:'INPUT_LIGHT', SWITCH:'SWITCH', A48V_FRONT:'A48V_FRONT', LEFT_LOCK_PIN_CURRENT:'LEFT_LOCK_PIN_CURRENT', RIGHT_LOCK_PIN_CURRENT:'RIGHT_LOCK_PIN_CURRENT', TRAILER_INFO_RESISTANCE:'TRAILER_INFO_RESISTANCE', ERROR_INFO:'ERROR_INFO', DISTANCE_INFO:'DISTANCE_INFO', NO_OF_COUPLINGS_INFO:'NO_OF_COUPLINGS_INFO', LOGG:'LOGG', MANUAL_OUTPUT:'MANUAL_OUTPUT', SEMI_AUTOMATIC_STEPPING:'SEMI_AUTOMATIC_STEPPING', EEPROM:'EEPROM', SEC_REQ:'SEC_REQ', CYCLE_TIME:'CYCLE_TIME'}

cfg_index = {RANGE_24V_FRONT:'RANGE_24V_FRONT', RANGE_24V_REAR:'RANGE_24V_REAR', RANGE_48V_FRONT:'RANGE_48V_FRONT', RANGE_48V_REAR:'RANGE_48V_REAR', RANGE_CURR_LEFT_PIN:'RANGE_CURR_LEFT_PIN', RANGE_CURR_RIGHT_PIN:'RANGE_CURR_RIGHT_PIN', COUPLING_VARIANT:'COUPLING_VARIANT', NODE_TYPE:'NODE_TYPE', VERSION:'VERSION', ART_NO:'ART_NO', SERIAL_NO:'SERIAL_NO', PULLUP_PULLDOWN:'PULLUP_PULLDOWN', CLEAR_EEPROM: 'CLEAR_EEPROM', VOLTAGE_WINDOW:'VOLTAGE_WINDOW', VOLTAGE_FACTOR:'VOLTAGE_FACTOR', TEMP_VALUE_MODE:'TEMP_VALUE_MODE', SPEED_FACTOR:'SPEED_FACTOR', XA13_FACTOR:'XA13_FACTOR', MANOUVER_MODE:'MANOUVER_MODE', CFG_REQ:'CFG_REQ'}

def bin(byte):
    return ''.join([str((byte >> i) & 0x01) for i in range(8)])

def prim_tx(m):
    return ' '.join([bin(d) for d in m.msg])

prim_rx = prim_tx

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
        elif index in (VOLTAGE_INT, VOLTAGE_EXT, A48V_FRONT, A48V_REAR):
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %.1fV' % (sec_index[index], val / 10.0)
        elif index in (READ_UART1, SEND_UART1):
            s = "'%s'" % ''.join([mychr(c) for c in m.msg[2:]])
            d = '[%s]' % ', '.join([('%02X' % c) for c in m.msg[2:]])
            return '%s %s %s' % (sec_index[index], s, d)
        elif index == SPEED_A:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %3.2f km/h' % (sec_index[index], val / 256.0)
        elif index == SUMMER_FREQUENCY:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %d Hz' % (sec_index[index], val)
        else:
            vals = [((m.msg[i] << 8) + m.msg[i + 1]) for i in range(2, m.dlc(), 2)]
            s = ', '.join([('0x%04X' % x) for x in vals])
            return '%s %s' % (sec_index[index], s)
    except Exception, e:
        print '*', e, type(e)
        print '*', m
        raise

sec_rx = sec_tx

def cfg_tx(m):
    try:
        index = (m.msg[0] << 8) + m.msg[1]
        if index == CFG_REQ:
            val = (m.msg[2] << 8) + m.msg[3]
            return '%s %s' % (cfg_index[index], cfg_index[val])
        else:
            vals = [((m.msg[i] << 8) + m.msg[i + 1]) for i in range(2, m.dlc(), 2)]
            s = ', '.join([('0x%04X' % x) for x in vals])
            return '%s %s' % (cfg_index[index], s)
    except Exception, e:
        print '*', e, type(e)
        print '*', m
        raise

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

def __filter(msg):
    global cnt
    global old_in_time
    global old_out_time
    try:
        cnt += 1
        if msg.addr() == 2:
            return True
        #if msg.group() in (IN, OUT):
            #return True
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

f = '%s\t%s\t%s\t%s\t%s'
ending = re.compile(r', 10, 03,? ?')

def dle_unpad(s):
    return s.replace('10, 10', '10')

def d2cm(d, t):
    cm = canmsg.CanMsg()
    cm.id = (int(d[0], 16) << 8) | int(d[1], 16)
    cm.msg = [int(x, 16) for x in d[2:]]
    cm.time = int(float(t) * 1000)
    return cm

s_cnt = 0
def out(t):
    global s_cnt
    s_cnt += 1
    cm = d2cm(t[4].split(', '), t[2])
    print 'S%05d %s\t%s\t%s' % (s_cnt, t[0], t[1], format(cm))
    sys.stdout.flush()

MEM = {'R':['', None], 'S':['', None]}

def foo(o):
    mem = MEM[o[2][0]]
    if mem[0]:
        s = dle_unpad(mem[0] + ', ' + o[-1])
        d = ending.split(s)
        if len(d) > 1:
            out((o[0], mem[1][0], o[1], o[2], d[0]))
            for data in d[1:-1]:
                out((o[0], o[0], o[1], o[2], data))
    else:
        s = dle_unpad(o[-1])
        d = ending.split(s)
        if len(d) > 1:
            for data in d[:-1]:
                out((o[0], o[0], o[1], o[2], data))
    mem[1] = o[0:-1]
    mem[0] = d[-1]

barre  = re.compile(r'(\d+)\s(\S+)\s\([^\)]+\)\s[^:]+: (READ|SEND)_UART1\s+\'[^\']*\'\s+\[(.+)\]')
def bar(l):
    o = barre.match(l)
    if o:
        foo(o.groups()) 

def parse_uart():
    for l in sys.stdin:
        bar(l)

def main():
    parse_uart()

if __name__ == '__main__':
    main()

def format(msg):
    m = ', '.join(['%02X' % x for x in msg.msg])
    t = msg.time / 1000.0
    st = msg.stcan()
    s = '%06d %08.3f (%03X:%s) [%s]: %s' % (cnt, t, msg.id, st, m, fmt(msg))
    bar(s)
    return s

def load_uart(ch):
    m = CanMsg()
    m.id = (SEC << 9) | (1 << 3) | OUT
    m.msg = [0x00, WRITE_UART1] + [ord(str(x)) for x in range(6)]
    for i in range(35):
        ch.write(m)

action_dict = {'l':load_uart}
