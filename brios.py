#!/bin/env python
import canmsg
import kvaser
import sys
import time

def debug(str):
    sys.stdout.write(str + '\n')
    sys.stdout.flush()

class StateMachine(object):
    def __init__(self):
        self.states = {}

    def add_state(self, name, func):
        self.states[name.upper()] = func

    def execute(self, start, arg):
        if not start:
            start = 'INIT'
        state = start
        while state:
            debug('state: {0:s}'.format(state))
            state, arg = self.states[state](arg)

slave = 0x01
master = 0x3E
pollrate = 1000
refreshrate = pollrate

EXPLICIT_CON = 'EXPLICIT_CON'
RESET = 'RESET'
SET_POLL_COS = 'SET_POLL_COS'
SET_POLL_RATE = 'SET_POLL_RATE'
SET_COS_RATE = 'SET_COS_RATE'
EXPLICIT_CON_RELEASE = 'EXPLICIT_CON_RELEASE'
POLL = 'POLL'

RES_OK = 'RES_OK'
RES_ERROR = 'RES_ERROR'
RES_UNKNOWN = 'RES_UNKNOWN'
RES_TIMEOUT = 'RES_TIMEOUT'

def command(pd, id, data, response=True, timeout=0.0):
    m = canmsg.CanMsg(id=id, data=data)
    pd.channel.write(m)
    T0 = time.time()
    #debug(str(m))
    while response:
        r = pd.channel.read()
        if not r:
            if timeout > 0.0:
                if time.time() - T0 > timeout:
                    return RES_TIMEOUT
            time.sleep(0.01)
            continue
        #debug(str(r))
        if r.id == 0x403 + 8 * slave:
            if r.data[1] == data[1] + 0x80:
                debug('got response')
                return RES_OK
            elif r.data[1] == 0x94:
                debug('error response')
                return RES_ERROR
            else:
                debug('unknown response')
                return RES_UNKNOWN
        elif r.id == 0x3C0 + slave:
            pd.IX = r.data[0]
            debug(str(pd))
            return RES_OK
        elif r.id == 0x340 + slave:
            pd.IX = r.data[0]
            debug(str(pd))

def explicit_con(pd):
    id = 0x406 + 8 * slave
    data = [master, 0x4B, 3, 1, 1, master]
    res = command(pd, id, data, timeout=1.0)
    if RES_OK == res:
        return (RESET, pd)
    debug(res)
    return (EXPLICIT_CON, pd)

def explicit_con_release(pd):
    id = 0x406 + 8 * slave
    data = [master, 0x4C, 3, 1, 1]
    command(pd, id, data)
    return (POLL, pd)

def reset(pd):
    id = 0x404 + 8 * slave
    data = [master, 0x5, 1, 1, 0]
    command(pd, id, data, response=False)
    time.sleep(5)
    return (SET_POLL_COS, pd)

def set_poll_cos(pd):
    id = 0x406 + 8 * slave
    data = [master, 0x4B, 0x03, 0x01, 0x53, master]
    command(pd, id, data)
    return (SET_POLL_RATE, pd)

def set_poll_rate(pd):
    prl = pollrate & 0xFF
    prh = (pollrate >> 8) & 0xFF
    id = 0x404 + 8 * slave
    data = [master, 0x10, 0x05, 0x02, 0x09, prl, prh]
    command(pd, id, data)
    return (SET_COS_RATE, pd)

def set_cos_rate(pd):
    rrl = refreshrate & 0xFF
    rrh = (refreshrate >> 8) & 0xFF
    id = 0x404 + 8 * slave
    data = [master, 0x10, 0x05, 0x04, 0x09, rrl, rrh]
    command(pd, id, data)
    return (POLL, pd)

def poll(pd):
    id = 0x405 + 8 * slave
    data = [pd.QX]
    T = time.time()
    T0 = T
    pr = pollrate / 1000.0
    while True:
        T = time.time()
        if T - T0 > pr:
            T0 = T
            data[0] = pd.QX
            command(pd, id, data)
        m = pd.channel.read()
        if m:
            if m.id == 0x340 + slave:
                pd.IX = m.data[0]
                debug(str(pd))
    return (None, pd)

class ProcessData(object):
    def __init__(self):
        self.channel = kvaser.KvaserCanChannel(channel=0, bitrate=kvaser.canBITRATE_125K)
        self.QX = 0

    def __str__(self):
        return 'QX: {0.QX:X}, IX: {0.IX:X}'.format(self)

def main():
    try:
        sm = StateMachine()
        sm.add_state(EXPLICIT_CON, explicit_con)
        sm.add_state(EXPLICIT_CON_RELEASE, explicit_con_release)
        sm.add_state(RESET, reset)
        sm.add_state(SET_COS_RATE, set_cos_rate)
        sm.add_state(SET_POLL_RATE, set_poll_rate)
        sm.add_state(SET_POLL_COS, set_poll_cos)
        sm.add_state(POLL, poll)
        sm.execute(EXPLICIT_CON, ProcessData())
    finally:
        pass

if __name__ == '__main__':
    main()

