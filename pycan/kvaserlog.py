import sys
import logging
import logging.handlers
import time

from pycan import kvaser
from pycan import canmsg

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
        self.logger.info(s)

def info(s):
    pass

def run(ch):
    def t(t0=time.time()):
        return time.time() - t0
    def cnt_info(cnt):
        fmt = '{0}: logged {1} messages, {2:.3f}/s'
        s = fmt.format(time.ctime(), cnt, cnt / t())
        info(s)
    T0 = t()
    cnt = 0
    cnt_info(cnt)
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

def main():
    global info
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--pure', action='store_true'
            , help='do not use the default BiCAN format')
    p.add_argument('-v', '--verbose', action='store_true'
            , help='print informational messages')
    p.add_argument('-c', '--channel', type=int, default=0
            , help='select CAN channel, default=%(default)s')
    p.add_argument('-b', '--bitrate', type=int, default=125000
            , help='select CAN bitrate, default=%(default)s')
    p.add_argument('logfile', default='', nargs='?'
            , help='file name for rotating log, default=%(default)s')
    args = p.parse_args()
    if not args.pure:
        canmsg.format_set(canmsg.FORMAT_BICAN)
    bitrate = kvaser.bitrate_as_number(args.bitrate)
    if bitrate is None:
        sys.stderr.write('Unknown bitrate: {}\n'.format(bitrate))
        sys.exit(1)
    if args.verbose:
        info = lambda s: logger.log(s)
    try:
        logger = Logger(args.logfile)
        ch = kvaser.KvaserCanChannel(channel=args.channel, bitrate=bitrate,
                logger=logger)
        s = 'channel: {}, bitrate: {}\n'.format(args.channel, bitrate)
        info(s)
        run(ch)
    except KeyboardInterrupt:
        pass
    except kvaser.KvaserException as e:
        sys.stderr.write(str(e) + '\n')

