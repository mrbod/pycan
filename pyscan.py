#!/usr/bin/env python
import os
import sys
import time
import getopt
import signal
import termios
import fcntl
import exceptions
import canmsg
import pycan

filterfile = None
filter_func = None
format_func = str
action_dict = {}
bitrate = 125
channel = 0
address = []
group = []
types = []

def dummy_action(ch):
    print 'dummy_action(%c)' % ch

def child(w):
    while True:
        try:
            time.sleep(0.01)
            c = sys.stdin.read(1)
            os.write(w, c)
        except exceptions.IOError, e:
            pass

def parent(r, pid):
    flags = pycan.canOPEN_EXCLUSIVE | pycan.canOPEN_ACCEPT_VIRTUAL
    ch = pycan.CanChannel(channel, bitrate, flags)
    while True:
        m = ch.read()
        if m:
            if group and not (m.group() in group):
                continue
            if address and not (m.addr() in address):
                continue
            if types and not (m.type() in types):
                continue
            if filter_func and not filter_func(m):
                continue
            print format_func(m)
        else:
            sys.stdout.flush()
            time.sleep(0.01)

        if action_dict:
            try:
                c = os.read(r, 1)
                action_dict.get(c, dummy_action)(ch)
            except exceptions.OSError, e:
                pass
            except exceptions.TypeError, e:
                print e
            except Exception, e:
                print type(e)
                print e
                raise

def exit(pid):
    if pid != 0:
        os.kill(pid, signal.SIGKILL)
        os.wait()

def dofork():
    if not action_dict:
        parent(None, 0)
        return
    (r, w) = os.pipe()
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(r, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    pid = os.fork()
    try:
        if pid == 0:
            child(w)
        else:
            parent(r, pid)
    except KeyboardInterrupt:
        exit(pid)
    except Exception, e:
        print e
        exit(pid)

def main():
    global filterfile
    global filter_func
    global format_func
    global action_dict
    global bitrate
    global channel
    global address
    global group
    global types

    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:b:a:g:t:f:")
    except getopt.GetoptError, e:
        print 'Usage: %s [-c <channel>] [-b <bitrate>]' % (sys.argv[0],)
        print '\t-c channel, default %d' % channel
        print '\t-b bitrate, default %d' % bitrate
        print '\t-f filter, load file as filter'
        print '\t-a address to show, can be repeated'
        print '\t-g group to show, can be repeated'
        print '\t-t type to show, can be repeated'
        print
        print >>sys.stderr, e
        sys.exit(1)

    for o in opts:
        if o[0] == '-c':
            channel = int(o[1])
        elif o[0] == '-b':
            bitrate = int(o[1])
        elif o[0] == '-a':
            address.append(int(o[1]))
        elif o[0] == '-g':
            group.append(int(o[1]))
        elif o[0] == '-t':
            types.append(int(o[1]))
        elif o[0] == '-f':
            filterfile = o[1]

    if filterfile:
        filterdict = canmsg.__dict__#{'CanMsg':canmsg.CanMsg}
        try:
            execfile(filterfile, filterdict)
        except IOError, e:
            print >>sys.stderr, 'Filter file: %s' % e
            sys.exit(1)
        try:
            filter_func = filterdict['filter']
        except KeyError, e:
            print >>sys.stderr, 'Using standard filter'
        try:
            format_func = filterdict['format']
        except KeyError, e:
            print >>sys.stderr, 'Using standard format'
        try:
            action_dict = filterdict['action_dict']
        except KeyError, e:
            print >>sys.stderr, 'Using standard actions'

    try:
        dofork()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    fd = sys.stdin.fileno()
    oldattr = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    try:
        try:
            oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

            main()
        finally:
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldattr)
