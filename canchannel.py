#!/usr/bin/env python
import sys
import os
import time
import canmsg
import optparse
import interface

def debug(str):
    sys.stdout.write(str)
    sys.stdout.flush()

def script_callback(option, optstr, value, parser):
    err = ''
    s_handler = 'handler'
    s_action = 'action'
    try:
        basedict = {}
        execfile(value, basedict)
        d = {}
        setattr(parser.values, option.dest, d)
        d[s_handler] = basedict.get(s_handler, None)
        d[s_action] = basedict.get(s_action, None)
        if d[s_handler] == None:
            err = 'No \'%s\' function specified in \'%s\'.' % (s_handler, value)
        elif d[s_action] == None:
            err = 'No \'%s\' function specified in \'%s\'.' % (s_action, value)
    except IOError, e:
        err = 'Filter file: %s' % e
    if err <> '':
        raise optparse.OptionValueError(err)

class CanChannelOptions(optparse.OptionParser):
    def __init__(self):
        print 'CanChannelOptions.__init__'
        optparse.OptionParser.__init__(self)
        self.add_options()
        self.parse_args()

    def add_options(self):
        print 'CanChannelOptions.add_options'
        self.add_option(
                '--script',
                dest='script', type='string', default=None,
                action='callback', callback=script_callback,
                help='python script for handling of sent and received messages and handling of user input',
                metavar='FILE')

class CanChannel(object):
    def __init__(self, options):
        print options.values
        self.starttime = time.time()
        self.options = options
        self.action_handler = None
        self.msg_handler = None
        self.T0 = self.starttime
        if self.options.values.script:
            self.action_handler = self.options.values.script.get('action', None)
            self.msg_handler = self.options.values.script.get('handler', None)
    
    def open(self):
        self.starttime = self.gettime()

    def close(self):
        print 'duration %.3fs' % (self.gettime() - self.starttime)

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time()

    def do_read(self):
        T = self.gettime()
        if T - self.T0 > 2:
            self.T0 = T
            m = canmsg.CanMsg()
            m.time = T - self.starttime
            return m
        return None

    def read(self):
        m = self.do_read()
        if m:
            m.channel = self
            if self.msg_handler:
                self.msg_handler(m)
        return m

    def do_write(self, msg):
        msg.time = self.gettime() - self.starttime

    def write(self, msg):
        self.do_write(msg)
        msg.channel = self
        msg.sent = True
        if self.msg_handler:
            self.msg_handler(msg)

    def action(self, key):
        if self.action_handler:
            self.action_handler(self, key)
        else:
            sys.stderr.write('No actions defined\n')

def main(channel_class):
    interface.main(channel_class, CanChannelOptions())

if __name__ == '__main__':
    try:
        main(CanChannel)
    except KeyboardInterrupt:
        pass

