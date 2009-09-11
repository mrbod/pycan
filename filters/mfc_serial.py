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

def bin(byte):
    return ''.join([str((byte >> i) & 0x01) for i in range(8)])

def prim_tx(m):
    return ' '.join([bin(d) for d in m.data])

prim_rx = prim_tx

def mychr(d):
    s = chr(d)
    if s.isalnum():
        return s
    else:
        return '.'

def sec_tx(m):
    try:
        index = (m.data[0] << 8) + m.data[1]
        if index == SEC_REQ:
            val = (m.data[2] << 8) + m.data[3]
            return 'secondary request %d' % index
        else:
            vals = [((m.data[i] << 8) + m.data[i + 1]) for i in range(2, m.dlc(), 2)]
            s = ', '.join([('0x%04X' % x) for x in vals])
            return 'secondary value %d %s' % (index, s)
    except Exception, e:
        print '*', e, type(e)
        print '*', m
        raise

sec_rx = sec_tx

def cfg_tx(m):
    try:
        index = (m.data[0] << 8) + m.data[1]
        if index == CFG_REQ:
            val = (m.data[2] << 8) + m.data[3]
            return 'config request %d' % val
        else:
            vals = [((m.data[i] << 8) + m.data[i + 1]) for i in range(2, m.dlc(), 2)]
            s = ', '.join([('0x%04X' % x) for x in vals])
            return 'config value %d %s' % (index, s)
    except Exception, e:
        print '*', e, type(e)
        print '*', m
        raise

cfg_rx = cfg_tx

def fmt(m):
    try:
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

f = '%s\t%s\t%s\t%s\t%s'
ending = re.compile(r', 10, 03,? ?')

def dle_unpad(s):
    return s.replace('10, 10', '10')

def d2cm(d, t):
    cm = canmsg.CanMsg()
    cm.id = (int(d[0], 16) << 8) | int(d[1], 16)
    cm.data = [int(x, 16) for x in d[2:]]
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
    m = ', '.join(['%02X' % x for x in msg.data])
    t = msg.time / 1000.0
    st = msg.stcan()
    s = '%06d %08.3f (%03X:%s) [%s]: %s' % (cnt, t, msg.id, st, m, fmt(msg))
    bar(s)
    return s

def load_uart(ch):
    m = canmsg.CanMsg()
    m.id = (SEC << 9) | (1 << 3) | OUT
    m.data = [0x00, WRITE_UART1] + [ord(str(x)) for x in range(6)]
    for i in range(35):
        ch.write(m)

log = True
T0 = time.time()
def filter(msg):
    global T0
    if log:
        print msg
        print fmt(msg)
    if msg.sent:
        pass
    else:
        if msg.group() == canmsg.GROUP_PIN:
            T = time.time()
            if T - T0 > 0.3:
                T0 = T
                primary(msg.channel)

def primary(ch):
    m = canmsg.CanMsg()
    m.id = (canmsg.GROUP_POUT << 9) | (61 << 3) | canmsg.TYPE_OUT
    m.data = [0, 1, 2, 3]
    ch.write(m)

address = 61
index = 22
value = 0
config = canmsg.CanMsg()
config.id = (CFG << 9) | (address << 3) | OUT
config.data = []

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

secondary = canmsg.CanMsg()
secondary.id = (SEC << 9) | (address << 3) | OUT
def send_secondary(ch, i, val):
    secondary.data = [0, i, (val >> 8) & 0xFF, val & 0xFF]
    ch.write(secondary)

config = canmsg.CanMsg()
config.id = (CFG << 9) | (address << 3) | OUT
def send_config(ch, i, val):
    config.data = [0, i, (val >> 8) & 0xFF, val & 0xFF]
    ch.write(config)

def toggle_bit(ch):
    if thread and thread.KeepAlive:
        thread.toggle_bit(index)
    else:
        print 'toggle_bit: thread dead'

def number_2_disp(ch):
    m = canmsg.CanMsg()
    m.id = secondary.id
    m.data = [0, 26, ((index & 0x7) << 5) | ((index & 0x3) << 3), 0, (value >> 8) & 0xFF, value & 0xFF]
    ch.write(m)

def text_2_disp(ch):
    m = canmsg.CanMsg()
    m.id = secondary.id
    m.data = [0, 25, 0x80, 0x44, ord('R'), ord('D')]
    ch.write(m)

def clear_screen(ch):
    m = canmsg.CanMsg()
    m.id = secondary.id
    m.data = [0, 25, 0x40, 0, ord('R'), ord('D')]
    ch.write(m)

def show_on_display(ch):
    m = canmsg.CanMsg()
    m.id = secondary.id
    s = 'antal6'
    m.data = [0, 30] + [ord(c) for c in s]
    ch.write(m)

def show_on_display2(ch):
    m = canmsg.CanMsg()
    m.id = secondary.id
    s = '$ES\0'
    m.data = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    s = '$LC1,5'
    m.data = [0, 30] + [ord(c) for c in s]
    ch.write(m)
    s = 'BArnEY'
    m.data = [0, 30] + [ord(c) for c in s]
    ch.write(m)

def toggle_log(ch):
    global log
    log = not log
    if log:
        print 'log on'
    else:
        print 'log off'

actions = {
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
        'l':toggle_log,
        }

def input(ch, key):
    if actions.has_key(key):
        actions[key](ch)
    else:
        print 'No action found for input: <%s>' % key
