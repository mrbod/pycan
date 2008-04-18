def filter(msg):
    if msg.addr() != 2:
        return False
    return True

def format(msg):
    m = ', '.join(['%02X' % x for x in msg.msg])
    st = '%02X %4s' % (msg.addr(), msg.sgroup())
    return '%s %8.3f   [%s]' % (st, msg.time / 1000.0, m)
