#!/usr/bin/env python
import sys
from ctypes import *
import time
from canmsg import CanMsg

if sys.platform == 'linux2':
    canlib32 = CDLL('libcanlib.so')
elif sys.platform == 'cygwin':
    canlib32 = CDLL('canlib32.dll')
elif sys.platform == 'win32':
    canlib32 = windll.canlib32
canlib32.canInitializeLibrary()

canBITRATE_1M = -1
canBITRATE_500K = -2
canBITRATE_250K = -3
canBITRATE_125K = -4
canBITRATE_100K = -5
canBITRATE_62K = -6
canBITRATE_50K = -7
canBITRATE_83K = -8
canBITRATE_10K = -9

canWANT_EXCLUSIVE = 0x0008
canWANT_EXTENDED = 0x0010
canWANT_VIRTUAL = 0x0020
canOPEN_EXCLUSIVE = canWANT_EXCLUSIVE
canOPEN_REQUIRE_EXTENDED = canWANT_EXTENDED
canOPEN_ACCEPT_VIRTUAL = canWANT_VIRTUAL
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200  # DLC can be greater than 8

canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0

canOK = 0
canERR_NOMSG = -2

class CanChannel(object):
    def __init__(self, channel, bitrate=canBITRATE_125K, flags=canOPEN_EXCLUSIVE | canOPEN_ACCEPT_VIRTUAL, on_msg=None, silent=False):
        self.channel = c_int(channel)
        self.bitrate = c_int(bitrate)
        self.flags = c_int(flags)
        self.handle = canlib32.canOpenChannel(self.channel, self.flags)
        if self.handle < 0:
            s = create_string_buffer(128)
            canlib32.canGetErrorText(self.handle, s, 128)
            raise Exception('%d: %s' % (self.handle, s.value))
        res = canlib32.canSetBusParams(self.handle, self.bitrate, 0, 0, 0, 0, 0)
        if res != canOK:
            s = create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        self.starttime = canlib32.canReadTimer(self.handle)
        res = canlib32.canBusOn(self.handle)
        if res != canOK:
            s = create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        if silent:
            res = canlib32.canSetBusOutputControl(self.handle, canDRIVER_SILENT)
            if res != canOK:
                s = create_string_buffer(128)
                canlib32.canGetErrorText(res, s, 128)
                raise Exception('%d: %s' % (res, s.value))
        else:
            res = canlib32.canSetBusOutputControl(self.handle, canDRIVER_NORMAL)
            if res != canOK:
                s = create_string_buffer(128)
                canlib32.canGetErrorText(res, s, 128)
                raise Exception('%d: %s' % (res, s.value))

    def __del__(self):
        canlib32.canClose(self.handle)

    def read(self):
        id = c_int()
        data = create_string_buffer(8)
        dlc = c_int()
        flags = c_int()
        time = c_int()
        res = canlib32.canRead(self.handle, byref(id), data, byref(dlc), byref(flags), byref(time))
        if res == canOK:
            d = [ord(data[i]) for i in range(dlc.value)]
            m = CanMsg(id.value, d, flags.value, time.value - self.starttime, channel=self)
            if on_msg:
                on_msg(m)
            return m
        if res != canERR_NOMSG:
            s = create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        return None

    def write(self, msg):
        d = ''.join([chr(x) for x in msg.msg])
        msg.time = canlib32.canReadTimer(self.handle) - self.starttime
        res = canlib32.canWrite(self.handle, msg.id, d, len(d), msg.flags)
        if on_msg:
            on_msg(m)

def main():
    ch = CanChannel(int(sys.argv[1]))
    while True:
        m = ch.read()
        while m:
            print m
            m = ch.read()
        sys.stdout.flush()
        time.sleep(0.001)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

