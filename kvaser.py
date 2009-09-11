#!/usr/bin/env python
import getopt
import canchannel
import sys
from ctypes import *
import time
import canmsg
import interface

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

class KvaserCanChannel(canchannel.CanChannel):
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
        canchannel.CanChannel.__init__(self, on_msg)

    def gettime(self):
        return canlib32.canReadTimer(self.handle)

    def __del__(self):
        canlib32.canClose(self.handle)

    def do_read(self):
        id = c_int()
        data = create_string_buffer(8)
        dlc = c_int()
        flags = c_int()
        time = c_int()
        res = canlib32.canRead(self.handle, byref(id), data, byref(dlc), byref(flags), byref(time))
        if res == canOK:
            T = self.gettime() - self.starttime
            d = [ord(data[i]) for i in range(dlc.value)]
            m = canmsg.CanMsg(id.value, d, flags.value, T, channel=self)
            return m
        if res != canERR_NOMSG:
            s = create_string_buffer(128)
            canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        return None

    def do_write(self, msg):
        d = ''.join([chr(x) for x in msg.data])
        res = canlib32.canWrite(self.handle, msg.id, d, len(d), msg.flags)
        msg.time = self.gettime() - self.starttime

def usage():
    prg_name = os.path.basename(sys.argv[0])
    print 'Usage: %s [options]' % (prg_name,)
    print
    print 'Options:'
    print '\t-c channel, default %d' % channel
    print '\t-b bitrate, default %d' % bitrate
    print '\t-s silent, do not participate in CAN traffic'
    print '\t-f FILE, load FILE as config file'
    print '\t-a address to show, can be repeated'
    print '\t-g group to show, can be repeated'
    print '\t-t type to show, can be repeated'

class KvaserOptions():
    def __init__(self):
        self.channel = 0
        self.bitrate = canBITRATE_125K
        self.silent = False
        self.actions = None
        self.handler = None

        try:
            opts, args = getopt.getopt(sys.argv[1:], "hc:b:a:g:t:f:s")
        except getopt.GetoptError, e:
            usage()
            print
            print >>sys.stderr, e
            sys.exit(1)

        filterfile = None

        for o in opts:
            if o[0] == '-h':
                usage()
                sys.exit(0)
            elif o[0] == '-c':
                self.channel = int(o[1])
            elif o[0] == '-b':
                self.bitrate = int(o[1])
            elif o[0] == '-f':
                filterfile = o[1]
            elif o[0] == '-s':
                self.silent = True

        if filterfile:
            filterdict = canmsg.__dict__
            try:
                execfile(filterfile, filterdict)
            except IOError, e:
                print >>sys.stderr, 'Filter file: %s' % e
                sys.exit(1)
            try:
                self.handler = filterdict['handler']
            except KeyError, e:
                print >>sys.stderr, 'Using standard format'
            try:
                self.actions = filterdict['actions']
            except KeyError, e:
                print >>sys.stderr, 'Using standard actions'

def main():
    o = KvaserOptions()
    flags = canOPEN_EXCLUSIVE | canOPEN_ACCEPT_VIRTUAL
    ch = KvaserCanChannel(o.channel, bitrate=o.bitrate, silent=o.silent, on_msg=o.handler)
    interface.main(ch, o.actions)
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

