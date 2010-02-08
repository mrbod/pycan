#!/usr/bin/env python
import canchannel
import sys
import os
from ctypes import c_int, byref, create_string_buffer
import ctypes.util
import time
import canmsg
import interface

if sys.platform == 'linux2':
    canlib32 = ctypes.CDLL('libcanlib.so')
elif sys.platform == 'cygwin':
    canlib32 = ctypes.CDLL('canlib32.dll')
elif sys.platform == 'win32':
    canlib32 = ctypes.windll.canlib32
canlib32.canInitializeLibrary()
print canlib32
print dir(canlib32)

canBITRATE_1M = -1
canBITRATE_500K = -2
canBITRATE_250K = -3
canBITRATE_125K = -4
canBITRATE_100K = -5
canBITRATE_62K = -6
canBITRATE_50K = -7
canBITRATE_83K = -8
canBITRATE_10K = -9
bitrates = {
        canBITRATE_1M: '1M',
        canBITRATE_500K: '500K',
        canBITRATE_250K: '250K',
        canBITRATE_125K: '125K',
        canBITRATE_100K: '100K',
        canBITRATE_62K: '62K',
        canBITRATE_50K: '50K',
        canBITRATE_83K: '83K',
        canBITRATE_10K: '10K'
        }

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

def debug(str):
    sys.stdout.write(str)
    sys.stdout.flush()

class KvaserCanChannel(canchannel.CanChannel):
    def __init__(self, options):
        canchannel.CanChannel.__init__(self, options)
        self.channel = ctypes.c_int(options.values.channel)
        self.bitrate = ctypes.c_int(options.values.bitrate)
        self.flags = ctypes.c_int(canOPEN_ACCEPT_VIRTUAL)# | canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED)
        self.handle = canlib32.canOpenChannel(self.channel, self.flags)
        if self.handle < 0:
            s = ctypes.create_string_buffer(128)
            canlib32.canGetErrorText(self.handle, s, 128)
            raise Exception('canOpenChannel=%d: %s' % (self.handle, s.value))
        res = canlib32.canSetBusParams(self.handle, self.bitrate, 0, 0, 0, 0, 0)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('canSetBusParams=%d: %s' % (res, s.value))
        res = canlib32.canBusOn(self.handle)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('canBusOn=%d: %s' % (res, s.value))
        if options.values.silent:
            res = canlib32.canSetBusOutputControl(self.handle, canDRIVER_SILENT)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                canlib32.canGetErrorText(res, s, 128)
                raise Exception('canSetBusOutputControl=%d: %s' % (res, s.value))
        else:
            res = canlib32.canSetBusOutputControl(self.handle, canDRIVER_NORMAL)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                canlib32.canGetErrorText(res, s, 128)
                raise Exception('canSetBusOutputControl=%d: %s' % (res, s.value))

    #def gettime(self):
        #return canlib32.canReadTimer(self.handle)

    def __del__(self):
        canlib32.canClose(self.handle)

    def do_read(self):
        id = ctypes.c_int()
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_int()
        flags = ctypes.c_int()
        time = ctypes.c_int()
        res = canlib32.canRead(self.handle, ctypes.byref(id), data, ctypes.byref(dlc), ctypes.byref(flags), ctypes.byref(time))
        if res == canOK:
            T = self.gettime() - self.starttime
            d = [ord(data[i]) for i in range(dlc.value)]
            m = canmsg.CanMsg(id.value, d, flags.value, T, channel=self)
            return m
        if res != canERR_NOMSG:
            s = ctypes.create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        return None

    def do_write(self, msg):
        d = ''.join([chr(x) for x in msg.data])
        res = canlib32.canWrite(self.handle, msg.id, d, len(d), msg.flags)
        msg.time = self.gettime() - self.starttime


class KvaserOptions(canchannel.CanChannelOptions):
    def __init__(self):
        print 'KvaserOptions.__init__'
        canchannel.CanChannelOptions.__init__(self)

    def add_options(self):
        print 'KvaserOptions.add_options'
        canchannel.CanChannelOptions.add_options(self)
        def bitrate_callback(option, optstr, value, parser):
            setattr(parser.values, option.dest, None)
            for k, v in bitrates.items():
                if v == value.upper():
                    setattr(parser.values, option.dest, k)
            if parser.values.bitrate == None:
                raise canchannel.optparse.OptionValueError('unknown bitrate <%s>' % value)
        self.add_option(
                '-c', '--channel',
                dest='channel', type='int', default=0,
                help='desired channel',
                metavar='CHANNEL')
        self.add_option(
                '-b', '--bitrate',
                dest='bitrate', type='string', default=canBITRATE_125K,
                action='callback', callback=bitrate_callback,
                help='desired bitrate (%s)' % ', '.join(bitrates.values()),
                metavar='BITRATE')
        self.add_option(
                '-s', '--silent',
                action='store_true', dest='silent', default=False,
                help='if a channel is silent it does not participate in CAN traffic',
                metavar='SILENT')

def main():
    interface.main(KvaserCanChannel, KvaserOptions())

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

