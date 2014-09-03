import sys
import logging
import logging.handlers
import time

from pycan import kvaser
from pycan import canmsg

def create_logger(filename):
    #handler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=10000000, backupCount=100000)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger = logging.getLogger('CANLOG')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

def run(ch):
    logger = create_logger('log')
    def log(txt):
        logger.info(txt)
    def info(c):
        t = time.ctime()
        sys.stderr.write('{0}: logged {1} messages\n'.format(t, c))
        sys.stderr.flush()
    T0 = time.time()
    cnt = 0
    info(cnt)
    try:
        while True:
            m = ch.read()
            if m:
                log(str(m))
                cnt += 1
            else:
                time.sleep(0.010)
            T = time.time()
            if T - T0 > 10.0:
                info(cnt)
                T0 = T
    finally:
        info(cnt)

def main():
    canmsg.format_set(canmsg.FORMAT_BICAN)
    channel = 0
    bitrate = 125000
    try:
        tmp = int(sys.argv[1])
        if tmp >= 10:
            bitrate = tmp
        else:
            channel = tmp
            try:
                tmp = int(sys.argv[2])
                bitrate = tmp
            except IndexError:
                pass
    except IndexError:
        pass
    try:
        ch = kvaser.KvaserCanChannel(channel=channel, bitrate=bitrate)
        sys.stderr.write('channel: {}, bitrate: {}\n'.format(channel, bitrate))
        run(ch)
    except KeyboardInterrupt:
        pass
    except kvaser.KvaserException as e:
        sys.stderr.write(str(e) + '\n')

