#!/usr/bin/env python
import os
import sys
import time
import getopt
import signal
import termios
import fcntl
import exceptions

input_handler = None

def set_input_handler(handler):
    global input_handler
    input_handler = handler

def child(w):
    while True:
        try:
            time.sleep(0.01)
            c = sys.stdin.read(1)
            os.write(w, c)
        except exceptions.IOError, e:
            pass
    sys.stderr.write('********** CHILD GONE *********\n')

def parent(channel_class, options, r):
    oldflags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(r, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    ch = channel_class(options)

    if input_handler == None:
        while True:
            if not ch.read():
                time.sleep(0.01)
    else:
        while True:
            if not ch.read():
                sys.stdout.flush()
                try:
                    c = os.read(r, 1)
                    input_handler(ch, c)
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

fd = sys.stdin.fileno()

def dofork(channel_class, options):
    (r, w) = os.pipe()
    pid = os.fork()
    try:
        if pid == 0:
            child(w)
        else:
            parent(channel_class, options, r)
    except KeyboardInterrupt:
        exit(pid)
    except Exception, e:
        print e
        exit(pid)

def main(channel_class, options):
    oldattr = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    try:
        try:
            oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
            try:
                dofork(channel_class, options)
            except OSError:
                pass
            except KeyboardInterrupt:
                pass
        finally:
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, oldattr)

