#!/usr/bin/env python
import sys
import os
import time
import canmsg
import optparse
import interface

optionparser = optparse.OptionParser()

msg_filter = None

def set_msg_filter(filter):
    global msg_filter
    msg_filter = filter

class CanChannel(object):
    def __init__(self, options):
        self.starttime = time.time()
        self.options = options
    
    def open(self):
        self.starttime = self.gettime()

    def close(self):
        print 'duration %.3fs' % (self.gettime() - self.starttime)

    def __del__(self):
        self.close()

    def gettime(self):
        return time.time()

    def do_read(self):
        m = canmsg.CanMsg()
        m.time = self.gettime() - self.starttime
        return m

    def read(self):
        m = self.do_read()
        if m:
            m.channel = self
            if msg_filter:
                msg_filter(m)
        return m

    def do_write(self, msg):
        msg.time = self.gettime() - self.starttime

    def write(self, msg):
        self.do_write(msg)
        msg.channel = self
        msg.sent = True
        if msg_filter:
            msg_filter(msg)

    def user_action(self, key):
        if self.on_action:
            self.on_action(key)

def msghandler(m):
    print m

def parse_opts():
    optionparser.add_option(
            '-f', '--filter',
            dest='filter',
            help='python script for handling of sent and received messages and handling of user input',
            metavar='FILE')
    (o, args) = optionparser.parse_args()
    if o.filter != None:
        try:
            basedict = {}
            execfile(o.filter, basedict)
            try:
                filter = basedict['filter']
                set_msg_filter(filter)
            except KeyError, e:
                s = 'No \'filter\' function specified in \'%s\'.' % o.filter
                print >>sys.stderr, s
            try:
                input = basedict['input']
                interface.set_input_handler(input)
            except KeyError, e:
                s = 'No \'input\' function specified in \'%s\'.' % o.filter
                print >>sys.stderr, s
        except IOError, e:
            print >>sys.stderr, 'Filter file: %s' % e
            sys.exit(1)
    return o


def main(channel_class):
    o = parse_opts()
    interface.main(channel_class, o)

if __name__ == '__main__':
    try:
        main(CanChannel)
    except KeyboardInterrupt:
        pass

