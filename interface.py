#!/usr/bin/env python
import os
import sys
import time
import getopt
import signal
import termios
import fcntl
import exceptions

def debug(txt):
    sys.stdout.write(txt)
    sys.stdout.flush()

def child(w):
    debug('CHILD STARTING\n')
    try:
        while True:
            try:
                time.sleep(0.01)
                c = sys.stdin.read(1)
                os.write(w, c)
            except exceptions.IOError, e:
                pass
    finally:
        debug('CHILD GONE\n')

def parent(channel, r):
    oldflags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(r, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    debug('PARENT STARTING\n')
    try:
        while True:
            if channel.read():
                time.sleep(0.001)
            else:
                sys.stdout.flush()
                try:
                    c = os.read(r, 1)
                    if c:
                        channel.action_handler(c)
                    else:
                        time.sleep(0.001)
                except exceptions.OSError, e:
                    pass
                except exceptions.TypeError, e:
                    print e
                except Exception, e:
                    print type(e)
                    print e
                    raise
    finally:
        channel.exit_handler()
        debug('PARENT GONE\n')

def exit(pid):
    if pid != 0:
        os.kill(pid, signal.SIGKILL)
        os.wait()

def dofork(channel):
    (r, w) = os.pipe()
    pid = os.fork()
    try:
        if pid == 0:
            child(w)
        else:
            parent(channel, r)
    except KeyboardInterrupt:
        exit(pid)
    except Exception, e:
        print e
        exit(pid)

def main(channel):
    fd = sys.stdin.fileno()
    oldattr = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    try:
        try:
            oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
            try:
                dofork(channel)
            except OSError:
                pass
            except KeyboardInterrupt:
                pass
        finally:
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldattr)

