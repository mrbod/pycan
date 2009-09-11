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

def dummy_action(ch):
    print 'dummy_action(%s)' % ch

def child(w):
    while True:
        try:
            time.sleep(0.01)
            c = sys.stdin.read(1)
            os.write(w, c)
        except exceptions.IOError, e:
            pass
    sys.stderr.write('********** CHILD GONE *********\n')

def parent(channel, actions, r):
    if actions:
        while True:
            if not channel.read():
                sys.stdout.flush()
                try:
                    c = os.read(r, 1)
                    actions.get(c, dummy_action)(channel)
                except exceptions.OSError, e:
                    pass
                except exceptions.TypeError, e:
                    print e
                except Exception, e:
                    print type(e)
                    print e
                    raise
    else:
        while True:
            if not channel.read():
                time.sleep(0.01)
def exit(pid):
    if pid != 0:
        os.kill(pid, signal.SIGKILL)
        os.wait()

fd = sys.stdin.fileno()

def dofork(channel, actions):
    if not actions:
        parent(channel, actions, None)
        return
    (r, w) = os.pipe()
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(r, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    pid = os.fork()
    try:
        if pid == 0:
            child(w)
        else:
            parent(channel, actions, r)
    except KeyboardInterrupt:
        exit(pid)
    except Exception, e:
        print e
        exit(pid)

def main(channel, actions):
    oldattr = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    try:
        try:
            oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
            try:
                dofork(channel, actions)
            except OSError:
                pass
            except KeyboardInterrupt:
                pass
        finally:
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldattr)

