def filter(msg):
    if msg.addr() != 1:
        return False
    if msg.type() != 1:
        return False
    if msg.msg[1] != 22:
        return False
    return True

def format(msg):
    m = ', '.join(['%02X' % x for x in msg.msg])
    st = '%02X %4s' % (msg.addr(), msg.sgroup())
    v = ((msg.msg[2] << 8) + msg.msg[3]) / 10.0
    return '%s %8.3f   [%s] %.1fV' % (st, msg.time / 1000.0, m, v)
