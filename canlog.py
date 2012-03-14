#!/c/Progra~1/Python26/python
import sys
import logging
import logging.handlers
import PCANBasic
import time
import canmsg

def create_logger(filename):
    handler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=10000000, backupCount=100000)
    logger = logging.getLogger('CANLOG')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

logger = create_logger('log')

def log_msg(m):
    print m.ID, m.MSGTYPE, m.LEN, m.DATA
    data = '[' + ', '.join(['{0:02X}'.format(x) for x in m.DATA[0:m.LEN]]) + ']'
    txt = '{0:02X}, {1:d}, {2}, {3:d}'.format(m.ID, m.LEN, data, m.MSGTYPE)
    logger.info(txt)

def PrintErr(ch, code, subject='Error'):
    res, txt = ch.GetErrorText(code, 0)
    if res != PCANBasic.PCAN_ERROR_OK:
        txt = 'Unable to get error text'
    etxt = '{0:s}: {1:s}\n'.format(subject, txt)
    logger.info(etxt)
    sys.stderr.write(etxt) 
    sys.stderr.write('\n') 

time_offset = 0.0
def calc_time(ts):
    '''Convert timestamp to seconds describing the system time'''
    global time_offset
    tot_us = ts.micros + 1000 * ts.millis + 0xFFFFFFFF * 1000 * ts.millis_overflow
    tmp = tot_us / 1.0e6
    if time_offset == 0.0:
        time_offset = time.time() - tmp
    return tmp + time_offset

def get_msg(ch):
    '''Read a CAN message on channel ch'''
    status, msg, timestruct = ch.Read(PCANBasic.PCAN_USBBUS1)
    if status == PCANBasic.PCAN_ERROR_OK:
        T = calc_time(timestruct)
        m = canmsg.StCanMsg(id=msg.ID, data=msg.DATA[0:msg.LEN], time=T)
        return m
    elif status != PCANBasic.PCAN_ERROR_QRCVEMPTY:
        PrintErr(ch, status)
    return None

def filter(stcan_msg):
    '''Return True if message should be logged, False in other cases'''
    if stcan_msg.type() == 5:
        return False
    return True

total_cnt = 0
accepted_cnt = 0

def process(channel):
    '''Process messages coming in on channel'''
    global total_cnt
    global accepted_cnt
    T0 = time.time()
    tot_m = 0
    acc_m = 0
    interval = 5.0
    while True:
        msg = get_msg(channel)
        if msg != None:
            total_cnt += 1
            if filter(msg):
                logger.info(str(msg))
                accepted_cnt += 1
        else:
            T = time.time()
            dT = T - T0
            if dT > interval:
                T0 = T
                s = 'logged {0}({1:.3f}/s) of {2}({3:.3f}/s) messages'
                dtot = total_cnt - tot_m
                tot_m = total_cnt
                dacc = accepted_cnt - acc_m
                acc_m = accepted_cnt
                txt = s.format(acc_m, dacc / dT, tot_m, dtot / dT)
                print txt
            else:
                time.sleep(0.01)

def main():
    c = PCANBasic.PCANBasic()
    try:
        res = c.Initialize(PCANBasic.PCAN_USBBUS1, PCANBasic.PCAN_BAUD_125K)
        PrintErr(c, res, 'Initialize')
        res = c.Reset(PCANBasic.PCAN_USBBUS1)
        PrintErr(c, res, 'Reset')
        process(c)
    finally:
        res = c.Uninitialize(PCANBasic.PCAN_USBBUS1)
        PrintErr(c, res, 'Uninitialize')
        print 'read {0:d}, logged {1:d}\n'.format(total_cnt, accepted_cnt)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

