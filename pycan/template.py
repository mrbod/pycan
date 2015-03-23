template='''from pycan import canmsg

# General CAN support
# msg.can_id is the CAN message ID
# msg.extended is True if the message is extended(29 bit)
# msg.data is a list of data values

# BiCAN support
# msg.addr is the BiCAN address
# msg.group can be one of GROUP_PIN, GROUP_POUT, GROUP_SEC, GROUP_CFG
# msg.type can be one of TYPE_IN, TYPE_OUT, TYPE_MON

# a function named canfilter in the filter file will be used as a log filter
# a message is logged if 'canfilter' returns True
# this canfilter-function allways returns True, i.e. all messages are logged
def canfilter(msg):
    return True

# short example
def short_canfilter(msg):
    # this will return True if msg.addr is one of 3, 4 or 12
    return (msg.addr in [3, 4, 12])

# long example for illustration of concept
def long_canfilter(msg):
    msg.channel.log('you can add log text too')
    if msg.group == canmsg.GROUP_SEC:
        return False
    if msg.type == canmsg.TYPE_IN:
        return False
    if (msg.can_id == 123):
        if msg.dlc >= 3:
            if msg.data[2] == 0x12:
                # send a CAN message, beware of log loops....
                m = canmsg.CanMsg()
                m.addr = 7
                m.group = canmsg.GROUP_POUT
                m.type = canmsg.TYPE_OUT
                m.data = [1,2,3]
                msg.channel.write(m)
                return False
            elif msg.data[3] == 0x12:
                return True
        return True
    if (msg.addr in [20, 22]):
        return True
    if msg.dlc == 6:
        return True
    return False
'''
