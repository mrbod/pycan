#!/usr/bin/env python
import sys
import os
from ctypes import c_int, byref, create_string_buffer
import ctypes.util
import time
import canchannel
import canmsg
import optparse
import platform

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
        canMSG_RTR: 'canMSG_RTR',
        canMSG_STD: 'canMSG_STD',
        canMSG_EXT: 'canMSG_EXT',
        canMSG_WAKEUP: 'canMSG_WAKEUP',
        canMSG_NERR: 'canMSG_NERR',
        canMSG_ERROR_FRAME: 'canMSG_ERROR_FRAME',
        canMSG_TXACK: 'canMSG_TXACK',
        canMSG_TXRQ: 'canMSG_TXRQ',
        canMSGERR_HW_OVERRUN: 'canMSGERR_HW_OVERRUN',
        canMSGERR_SW_OVERRUN: 'canMSGERR_SW_OVERRUN',
        canMSGERR_STUFF: 'canMSGERR_STUFF',
        canMSGERR_FORM: 'canMSGERR_FORM',
        canMSGERR_CRC: 'canMSGERR_CRC',
        canMSGERR_BIT0: 'canMSGERR_BIT0',
        canMSGERR_BIT1: 'canMSGERR_BIT1',
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
        canBITRATE_1M: ('1M', '1000000'),
        canBITRATE_500K: ('500K', '500000'),
        canBITRATE_250K: ('250K', '250000'),
        canBITRATE_125K: ('125K', '125000'),
        canBITRATE_100K: ('100K', '100000'),
        canBITRATE_62K: ('62K', '62000'),
        canBITRATE_50K: ('50K', '50000'),
        canBITRATE_83K: ('83K', '83000'),
        canBITRATE_10K: ('10K', '10000')
        }
def bitrate_search(x):
    x = str(x)
    for k, v in bitrates.items():
        for br in v:
            if x == br:
                return k
    return None

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

# (bitrate, tseg1, tseg2, sjw, nosamp, syncmode)
bitrate_settings = {
        canBITRATE_1M: (1000000, 4, 3, 1, 1, 0),
        canBITRATE_500K: (500000, 4, 3, 1, 1, 0),
        canBITRATE_250K: (250000, 4, 3, 1, 1, 0),
        canBITRATE_125K: (125000, 10, 5, 1, 1, 0),
        canBITRATE_100K: (100000, 10, 5, 1, 1, 0),
        canBITRATE_83K: (83333, 5, 2, 2, 1, 0),
        canBITRATE_62K: (62500, 10, 5, 1, 1, 0),
        canBITRATE_50K: (50000, 10, 5, 1, 1, 0),
        canBITRATE_10K: (10000, 11, 4, 1, 1, 0)
        }

class KvaserException(Exception):
    pass

class KvaserCanChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=canBITRATE_125K, silent=False, **kwargs):
        self.canlib = None
        self.gettime = self.gettime_linux
        if sys.platform == 'linux2':
            self.canlib = ctypes.CDLL('libcanlib.so')
        elif sys.platform == 'cygwin':
            self.canlib = ctypes.CDLL('canlib32.dll')
        elif sys.platform == 'win32':
            self.canlib = ctypes.windll.canlib32
            self.gettime = self.gettime_windows
        else:
            s = 'Unknown platform: {0:s}'.format(sys.platform)
            raise KvaserException(s)
        self.canlib.canInitializeLibrary()
        self.channel = ctypes.c_int(channel)
        if bitrate not in bitrates.keys():
            br = bitrate_search(bitrate)
            if br is None:
                raise KvaserException('Unknown bitrate: {0}'.format(str(bitrate)))
            bitrate = br
        self.bitrate = ctypes.c_int(bitrate)
        self.silent = silent
        self.flags = ctypes.c_int(canWANT_EXTENDED | canOPEN_ACCEPT_VIRTUAL)
        self.handle = self.canlib.canOpenChannel(self.channel, self.flags)
        if self.handle < 0:
            s = ctypes.create_string_buffer(128)
            self.canlib.canGetErrorText(self.handle, s, 128)
            raise KvaserException('canOpenChannel(%d, 0x%X=%d: %s' % (channel, self.flags.value, self.handle, s.value))
        res = self.canlib.canSetBusParams(self.handle, *bitrate_settings[bitrate])
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            self.canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canSetBusParams=%d: %s' % (res, s.value))
        res = self.canlib.canBusOn(self.handle)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            self.canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canBusOn=%d: %s' % (res, s.value))
        if self.silent:
            res = self.canlib.canSetBusOutputControl(self.handle, canDRIVER_SILENT)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                self.canlib.canGetErrorText(res, s, 128)
                raise KvaserException('canSetBusOutputControl=%d: %s' % (res, s.value))
        else:
            res = self.canlib.canSetBusOutputControl(self.handle, canDRIVER_NORMAL)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                self.canlib.canGetErrorText(res, s, 128)
                raise KvaserException('canSetBusOutputControl=%d: %s' % (res, s.value))
        super(KvaserCanChannel, self).__init__(**kwargs)

    def set_baud(self, handle, baud):
        settings = bitrate_settings[baud]
        res = self.canlib.canSetBusParams(handle, *settings)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            self.canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canSetBusParams=%d: %s' % (res, s.value))

    def gettime_linux(self):
        time = ctypes.c_uint()
        self.canlib.canReadTimer(self.handle, ctypes.byref(time))
        return time.value / 1000.0

    def gettime_windows(self):
        x = self.canlib.canReadTimer(self.handle)
        return x / 1000.0

    def __del__(self):
        if self.canlib != None:
            self.canlib.canClose(self.handle)

    def do_read(self):
        id = ctypes.c_int()
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_int()
        flags = ctypes.c_int()
        T = ctypes.c_uint()
        res = self.canlib.canRead(self.handle, ctypes.byref(id), data, ctypes.byref(dlc), ctypes.byref(flags), ctypes.byref(T))
        if res == canOK:
            #T = self.gettime()
            t = T.value / 1000.0
            if flags.value & canMSG_ERROR_FRAME:
                m = canmsg.CanMsg(error_frame=True)
                return m
            d = [ord(data[i]) for i in range(dlc.value)]
            if flags.value & canMSG_EXT != 0:
                ext = True
            else:
                ext = False
            m = canmsg.CanMsg(id=id.value, data=d, extended=ext, time=t, channel=self)
            return m
        if res != canERR_NOMSG:
            s = ctypes.create_string_buffer(128)
            self.canlib.canGetErrorText(res, s, 128)
            raise KvaserException('%d: %s' % (res, s.value))
        time.sleep(0.001)
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
            res = self.canlib.canWrite(self.handle, msg.id, d, len(d), flags)
            if res == 0:
                msg.time = self.gettime()
                break
            if cnt % 10 == 0:
                self.info(5, 'written {0} times'.format(cnt))
            elif cnt > 10000:
                raise KvaserException('do_write failed(%d)' % res)

class KvaserOptions(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        def bitrate_callback(option, optstr, value, parser):
            setattr(parser.values, option.dest, bitrate_search(value))
            if parser.values.bitrate == None:
                raise canchannel.optparse.OptionValueError('unknown bitrate <%s>' % value)
        self.add_option(
                '-c', '--channel',
                dest='channel', type='int', default=0,
                help='desired channel',
                metavar='CHANNEL')
        x = [y[0] for y in bitrates.values()]
        self.add_option(
                '-b', '--bitrate',
                dest='bitrate', type='string', default=canBITRATE_125K,
                action='callback', callback=bitrate_callback,
                help='desired bitrate (%s)' % ', '.join(x),
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
    import interface
    import threading
    canmsg.format_set(canmsg.FORMAT_STCAN)

    # Example Kvaser subclass.
    # Useful as generic logger...
    class KCC(KvaserCanChannel):
        def __init__(self, channel=0, bitrate=canBITRATE_125K, silent=False):
            super(KCC, self).__init__(channel, bitrate, silent)
            self.ext = False
            self.pmode = False
            t = threading.Thread(target=self.primary_thread)
            t.daemon = True
            t.start()

        def primary_thread(self):
            time.sleep(1.0)
            while True:
                if not self.pmode:
                    time.sleep(0.1)
                    continue
                time.sleep(0.004)
                m = canmsg.CanMsg()
                m.extended = self.ext
                m.group = canmsg.GROUP_PIN
                m.type = canmsg.TYPE_IN
                m.addr = 0x0F
                m.data = [0x00, 0x00, 0xAA, 1]
                self.write(m)

        def action_handler(self, c):
            if c == 'e':
                self.ext = not self.ext
            elif c == 'p':
                self.pmode = not self.pmode
            elif c == 's':
                m = canmsg.CanMsg()
                m.extended = self.ext
                m.group = canmsg.GROUP_PIN
                m.type = canmsg.TYPE_IN
                m.addr = 0x0F
                m.data = [0x00, 0x63, 0x00, 0x1F]
                self.write(m)
            elif c == 'F':
                m = canmsg.CanMsg()
                m.group = canmsg.GROUP_POUT
                m.type = canmsg.TYPE_OUT
                m.addr = 1
                m.data = [0]
                self.write(m)
            elif c == 'f':
                m = canmsg.CanMsg()
                m.group = canmsg.GROUP_PIN
                m.type = canmsg.TYPE_IN
                m.addr = 1
                m.data = [0,0,0]
                self.write(m)
            elif c == 'l':
                for i in range(16):
                    m = canmsg.CanMsg()
                    m.extended = self.ext
                    m.id = 0x3F0
                    m.data = [i & 0xFF]
                    self.write(m)
                    time.sleep(.01)

    cc = KCC(channel=opts.channel, bitrate=opts.bitrate, silent=opts.silent)
    i = interface.Interface(cc)
    i.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

