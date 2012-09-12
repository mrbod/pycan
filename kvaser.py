#!/usr/bin/env python
import sys
import os
from ctypes import c_int, byref, create_string_buffer
import ctypes.util
import time
import canchannel
import canmsg
import stcan
import optparse
import interface

canMSG_RTR = 0x0001      # Message is a remote request
canMSG_STD = 0x0002      # Message has a standard ID
canMSG_EXT = 0x0004      # Message has an extended ID
canMSG_WAKEUP = 0x0008      # Message to be sent / was received in wakeup mode
canMSG_NERR = 0x0010      # NERR was active during the message
canMSG_ERROR_FRAME = 0x0020      # Message is an error frame
canMSG_TXACK = 0x0040      # Message is a TX ACK (msg is really sent)
canMSG_TXRQ = 0x0080      # Message is a TX REQUEST (msg is transfered to the chip)
canMSGERR_HW_OVERRUN = 0x0200      # HW buffer overrun
canMSGERR_SW_OVERRUN = 0x0400      # SW buffer overrun
canMSGERR_STUFF = 0x0800      # Stuff error
canMSGERR_FORM = 0x1000      # Form error
canMSGERR_CRC = 0x2000      # CRC error
canMSGERR_BIT0 = 0x4000      # Sent dom, read rec
canMSGERR_BIT1 = 0x8000      # Sent rec, read dom

flags_inv = {
        0x0001: 'canMSG_RTR',
        0x0002: 'canMSG_STD',
        0x0004: 'canMSG_EXT',
        0x0008: 'canMSG_WAKEUP',
        0x0010: 'canMSG_NERR',
        0x0020: 'canMSG_ERROR_FRAME',
        0x0040: 'canMSG_TXACK',
        0x0080: 'canMSG_TXRQ',
        0x0200: 'canMSGERR_HW_OVERRUN',
        0x0400: 'canMSGERR_SW_OVERRUN',
        0x0800: 'canMSGERR_STUFF',
        0x1000: 'canMSGERR_FORM',
        0x2000: 'canMSGERR_CRC',
        0x4000: 'canMSGERR_BIT0',
        0x8000: 'canMSGERR_BIT1',
        }

flag_texts = {
        canMSG_RTR: 'RTR',
        canMSG_STD: 'STD',
        canMSG_EXT: 'EXT',
        canMSG_WAKEUP: 'WAKEUP',
        canMSG_NERR: 'NERR',
        canMSG_ERROR_FRAME: 'ERROR_FRAME',
        canMSG_TXACK: 'TXACK',
        canMSG_TXRQ: 'TXRQ',
        canMSGERR_HW_OVERRUN: 'HW_OVERRUN',
        canMSGERR_SW_OVERRUN: 'SW_OVERRUN',
        canMSGERR_STUFF: 'STUFF',
        canMSGERR_FORM: 'FORM',
        canMSGERR_CRC: 'CRC',
        canMSGERR_BIT0: 'BIT0',
        canMSGERR_BIT1: 'BIT1',
        }

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

class KvaserCanChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=canBITRATE_125K, silent=False, msg_class=canmsg.CanMsg):
        self.canlib32 = None
        if sys.platform == 'linux2':
            self.canlib32 = ctypes.CDLL('libcanlib.so')
        elif sys.platform == 'cygwin':
            self.canlib32 = ctypes.CDLL('canlib32.dll')
        elif sys.platform == 'win32':
            self.canlib32 = ctypes.windll.canlib32
        else:
            raise Exception('Unknown platform: {0:s}'.format(sys.platform))
        self.canlib32.canInitializeLibrary()

        super(KvaserCanChannel, self).__init__(msg_class=msg_class)

        self.channel = ctypes.c_int(channel)
        self.bitrate = ctypes.c_int(bitrate)
        self.silent = silent
        self.flags = ctypes.c_int(canOPEN_ACCEPT_VIRTUAL | canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED)
        self.handle = self.canlib32.canOpenChannel(self.channel, self.flags)
        if self.handle < 0:
            s = ctypes.create_string_buffer(128)
            self.canlib32.canGetErrorText(self.handle, s, 128)
            raise Exception('canOpenChannel=%d: %s' % (self.handle, s.value))
        res = self.canlib32.canSetBusParams(self.handle, self.bitrate, 0, 0, 0, 0, 0)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            self.canlib32.canGetErrorText(res, s, 128)
            raise Exception('canSetBusParams=%d: %s' % (res, s.value))
        res = self.canlib32.canBusOn(self.handle)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            self.canlib32.canGetErrorText(res, s, 128)
            raise Exception('canBusOn=%d: %s' % (res, s.value))
        if self.silent:
            res = self.canlib32.canSetBusOutputControl(self.handle, canDRIVER_SILENT)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                self.canlib32.canGetErrorText(res, s, 128)
                raise Exception('canSetBusOutputControl=%d: %s' % (res, s.value))
        else:
            res = self.canlib32.canSetBusOutputControl(self.handle, canDRIVER_NORMAL)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                self.canlib32.canGetErrorText(res, s, 128)
                raise Exception('canSetBusOutputControl=%d: %s' % (res, s.value))

    #def gettime(self):
        #return self.canlib32.canReadTimer(self.handle) / 1000.0

    def __del__(self):
        if self.canlib32 != None:
            self.canlib32.canClose(self.handle)

    def do_read(self):
        id = ctypes.c_int()
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_int()
        flags = ctypes.c_int()
        time = ctypes.c_int()
        res = self.canlib32.canReadWait(self.handle, ctypes.byref(id), data, ctypes.byref(dlc), ctypes.byref(flags), ctypes.byref(time), -1)
        if res == canOK:
            T = self.gettime()
            d = [ord(data[i]) for i in range(dlc.value)]
            m = self.msg_class(id.value, d, flags.value, T, channel=self)
            return m
        if res != canERR_NOMSG:
            s = ctypes.create_string_buffer(128)
            self.canlib32.canGetErrorText(res, s, 128)
            raise Exception('%d: %s' % (res, s.value))
        return None

    def do_write(self, msg):
        d = ''.join([chr(x) for x in msg.data])
        cnt = 0
        if msg.extended:
            flags = canMSG_EXT
        else:
            flags = canMSG_STD
        while True:
            cnt += 1
            res = self.canlib32.canWrite(self.handle, msg.id, d, len(d), flags)
            if res == 0:
                break
            elif cnt % 50 == 0:
                self.info('written {0} times'.format(cnt))
            elif cnt > 10000:
                raise Exception('do_write failed(%d)' % res)
        msg.time = self.gettime()

class KvaserOptions(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        def bitrate_callback(option, optstr, value, parser):
            setattr(parser.values, option.dest, None)
            for k, v in bitrates.items():
                if v == value.upper():
                    setattr(parser.values, option.dest, k)
                elif v[:-1] == value:
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

def parse_args():
    return KvaserOptions().parse_args()

def main():
    opts, args = parse_args()

    # Example Kvaser subclass.
    # Useful as generic logger...
    class KCC(KvaserCanChannel):
        def __init__(self, channel=0, bitrate=canBITRATE_125K, silent=False):
            super(KCC, self).__init__(channel, bitrate, silent, msg_class=stcan.StCanMsg)

        def action_handler(self, c):
            if c == 'l':
                m = self.msg_class()
                m.id = (stcan.GROUP_PIN << 9) | (1 << 3) | stcan.TYPE_IN
                m.extended = False
                for i in range(100):
                    m.data = [i >> 8, i & 0xFF]
                    self.write(m)
            elif c == 's':
                m = self.msg_class()
                m.id = (stcan.GROUP_PIN << 9) | (1 << 3) | stcan.TYPE_IN
                m.extended = False
                m.data = [ord(c) for c in 'hejsan']
                self.write(m)
            else:
                try:
                    self.i += 1
                except:
                    self.i = 0
                m = self.msg_class()
                m.id = (stcan.GROUP_PIN << 27) | (1 << 3) | stcan.TYPE_IN
                m.extended = False
                m.data = [self.i & 0xFF]
                self.write(m)

    cc = KCC(channel=opts.channel, bitrate=opts.bitrate, silent=opts.silent)
    interface = interface.Interface(cc)
    interface.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

