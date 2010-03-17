import canmsg
import sys
import time
import threading

def debug(str):
    sys.stdout.write(str)
    sys.stdout.flush()

def send(ch):
    m = canmsg.CanMsg()
    m.id = 1 << 9
    m.data = []
    ch.write(m)

run_timing = False
timing_running = False
cnt = 0
T0 = 0.0
T1 = 0.0
def dump_stat():
    T = T1 - T0
    if T == 0.0:
        return
    f = cnt / T
    dT = 1 / f
    s = 'T=%.3f cnt=%d f=%.3f dT=%.8f\n' % (T, cnt, f, dT)
    sys.stderr.write(s)

def dump_msg(m):
    fmt = '%8.3f %03X %d:%s\n'
    s = fmt % (m.time, m.id, m.dlc(), m.data_str())
    sys.stdout.write(s)

show_sync = False
Tstat = 0.0
def handler(m):
    global cnt, T0, T1, Tstat
    global timing_running
    cnt += 1
    if run_timing:
        if timing_running:
            T1 = m.time
            if T1 - Tstat > 1.0:
                dump_stat()
                Tstat = T1
        else:
            timing_running = True
            cnt = 0
            T0 = m.time
            Tstat = T0
    dump_msg(m)

def action(channel, c):
    global run_timing, cnt
    global show_sync
    if c == 't':
        run_timing = not run_timing
        if not run_timing:
            timing_running = False
            dump_stat()
    elif c == 's':
        show_sync = not show_sync
    else:
        send(channel)

def exit():
    pass

