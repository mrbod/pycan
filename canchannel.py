#!/usr/bin/env python
import sys
import os
import time
import canmsg
import optparse
import interface
import threading
import logthread

logger = logthread.Logger()

class CanChannel(object):
    def __init__(self):
        self.starttime = time.time()
        self.T0 = self.gettime()
        self._write_lock = threading.Lock()
    
    def open(self):
        self.starttime = time.time()

    def close(self):
        self.log('duration %.3fs' % self.gettime())

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time() - self.starttime

    def do_read(self):
        T = self.gettime()
        if T - self.T0 > 2:
            self.T0 = T
            m = canmsg.CanMsg()
            m.time = T
            return m
        return None

    def read(self):
        m = None
        try:
            m = self.do_read()
        finally:
            pass
        if m:
            m.channel = self
            self.message_handler(m)
        return m

    def do_write(self, msg):
        msg.time = self.gettime()

    def write(self, msg):
        self._write_lock.acquire(True)
        try:
            self.do_write(msg)
        finally:
            self._write_lock.release()
        msg.channel = self
        msg.sent = True
        self.message_handler(msg)

    def log(self, x):
        logger.log(x)

    def action_handler(self, key):
        pass

    def message_handler(self, m):
        pass

    def exit_handler(self):
        pass

def script_parser(script):
    err = ''
    s_handler = 'message_handler'
    s_action = 'action_handler'
    s_exit = 'exit_handler'
    try:
        basedict = {}
        execfile(script, basedict)
        d = {}
        setattr(parser.values, option.dest, d)
        d[s_handler] = basedict.get(s_handler, None)
        d[s_action] = basedict.get(s_action, None)
        d[s_exit] = basedict.get(s_exit, None)
        if d[s_handler] == None:
            err = 'No \'%s\' function specified in \'%s\'.' % (s_handler, value)
        elif d[s_action] == None:
            err = 'No \'%s\' function specified in \'%s\'.' % (s_action, value)
        elif d[s_exit] == None:
            err = 'No \'%s\' function specified in \'%s\'.' % (s_exit, value)
    except IOError, e:
        err = 'Filter file: %s' % e
    if err <> '':
        raise optparse.OptionValueError(err)
    return d

def main(channel):
    try:
        interface.main(channel)
    finally:
        logger.active = False
        channel.exit_handler()

if __name__ == '__main__':
    try:
        class CCC(CanChannel):
            def message_handler(self, m):
                self.log(m)

        ch = CCC()
        main(ch)
    except KeyboardInterrupt:
        pass

