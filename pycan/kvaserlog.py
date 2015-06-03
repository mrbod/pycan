import sys
import os
import logging
import logging.handlers
import time

from pycan import kvaser
from pycan import canmsg

msgfilter = None

class Logger(object):
    def __init__(self, filename=''):
        self.logger = logging.getLogger('CANLOG')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(stream=sys.stdout)
        self.logger.addHandler(handler)
        if filename:
            handler = logging.handlers.RotatingFileHandler(filename=filename
                    , maxBytes=10000000, backupCount=100000)
            self.logger.addHandler(handler)

    def log(self, s):
        if msgfilter:
            if isinstance(s, canmsg.CanMsg):
                try:
                    l = msgfilter(s)
                except Exception as e:
                    s = 'exception in filter function: {}'
                    sys.stderr.write(s.format(str(e)))
                    sys.stderr.write('{}\n'.format(dir(canmsg.CanMsg)))
                    sys.exit(1)
                if l:
                    self.logger.info(s)
            else:
                self.logger.info(s)
        else:
            self.logger.info(s)


def info(s):
    pass

def run(ch):
    t0 = time.time()
    def t():
        return time.time() - t0
    def cnt_info(cnt):
        fmt = '{0}: logged {1} messages, {2:.3f}/s'
        T = t()
        if T > 0.0:
            s = fmt.format(time.ctime(), cnt, cnt / T)
            info(s)
    cnt = 0
    T0 = t0
    try:
        while True:
            if ch.read():
                cnt += 1
            else:
                time.sleep(0.010)
            T = t()
            if T - T0 > 10.0:
                cnt_info(cnt)
                T0 = T
    finally:
        cnt_info(cnt)

def write_template(fname):
    if os.path.exists(fname):
        sys.stderr.write('template not written, file {} exists\n'.format(fname))
        sys.exit(1)
    import template
    try:
        open(fname, "w").write(template.template)
    except Exception as e:
        sys.stderr.write('failed to write template: {}\n'.format(str(e)))
        sys.exit(1)

def load_filter(fname):
    global msgfilter
    try:
        data = open(fname).read()
    except IOError as e:
        sys.stderr.write('failed to read file "%s": %s\n' % (fname, str(e)))
        sys.exit(1)
    try:
        print(dir())
        exec(data)
        print(dir())
    except Exception as e:
        sys.stderr.write('failed to execute file "%s": %s\n' % (fname, str(e)))
        sys.exit(1)
    try:
        msgfilter = canfilter
    except Exception as e:
        s = 'no "canfilter" function found in file "%s": %s\n'
        sys.stderr.write(s % (fname, str(e)))
        sys.exit(1)

def main():
    global info
    import argparse
    p = argparse.ArgumentParser(description='''Log messages collected with a Kvaser CAN device.''')
    p.add_argument('-p', '--pure', action='store_true'
            , help='do not use the default BiCAN format')
    p.add_argument('-v', '--verbose', action='store_true'
            , help='print informational messages')
    p.add_argument('-f', '--filter', default='', metavar='FILE'
            , help='''filter file name. %(prog)s will import %(metavar)s and use
            a function named "canfilter" in the file as a log filter''')
    p.add_argument('-t', '--template', default='', metavar='FILE'
            , help='write a template filter to %(metavar)s and exit')
    p.add_argument('-c', '--channel', type=int, default=0
            , help='select CAN channel, default=%(default)s')
    p.add_argument('-b', '--bitrate', type=int, default=125000
            , help='select CAN bitrate, default=%(default)s')
    p.add_argument('-s', '--silent', action='store_true'
            , help='open channel in silent mode')
    p.add_argument('logfile', default='', nargs='?'
            , help='file name for rotating log, default=%(default)s')
    args = p.parse_args()
    if args.template:
        write_template(args.template)
        sys.exit(0)
    if not args.pure:
        canmsg.format_set(canmsg.FORMAT_BICAN)
    bitrate = kvaser.bitrate_as_number(args.bitrate)
    if bitrate is None:
        sys.stderr.write('Unknown bitrate: {}\n'.format(bitrate))
        sys.exit(1)
    if args.verbose:
        info = lambda s: logger.log(s)
    if args.filter:
        load_filter(args.filter)
    try:
        logger = Logger(args.logfile)
        ch = kvaser.KvaserCanChannel(channel=args.channel, bitrate=bitrate,
                silent=args.silent, logger=logger)
        s = 'channel: {}, bitrate: {}\n'.format(args.channel, bitrate)
        info(s)
        run(ch)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
    except kvaser.KvaserException as e:
        sys.stderr.write(str(e) + '\n')

