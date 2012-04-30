#!/usr/bin/env python
import sys
import logging
import logging.handlers
import time
import socketcan
import stcan

def create_logger(filename):
    handler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=10000000, backupCount=100000)
    logger = logging.getLogger('CANLOG')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

class StdOutLogger(object):
    def info(self, txt):
        sys.stdout.write(txt)
        sys.stdout.write('\n')

def log(txt):
    logger.info(txt)

def main():
    #ch = socketcan.SocketCanChannel(int(sys.argv[1]))
    ch = socketcan.SocketCanChannel(int(sys.argv[1]), msg_class=stcan.StCanMsg)
    T0 = time.time()
    cnt = 0
    while True:
        m = ch.read()
        if m:
            log(str(m))
            cnt += 1
            T = time.time()
            if T - T0 > 10.0:
                sys.stderr.write('{0}: logged {1} messages\n'.format(time.ctime(), cnt))
                sys.stderr.flush()
                T0 = T
        else:
            time.sleep(0.010)

if __name__ == '__main__':
    logger = None
    for a in sys.argv[1:]:
        if (a == '-') or (a == 'stdout'):
            logger = StdOutLogger()
    if logger == None:
        logger = create_logger('log')
    try:
        main()
    except KeyboardInterrupt:
        pass

