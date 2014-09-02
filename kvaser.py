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
        '1000K': (1000000, canBITRATE_1M),
        '500K': (500000, canBITRATE_500K),
        '250K': (250000, canBITRATE_250K),
        '125K': (125000, canBITRATE_125K),
        '100K': (100000, canBITRATE_100K),
        '62K': (62000, canBITRATE_62K),
        '50K': (50000, canBITRATE_50K),
        '83K': (83000, canBITRATE_83K),
        '10K': (10000, canBITRATE_10K)
        }

def bitrate_search(x):
    for k, v in bitrates.items():
        if x == k:
            return v[1]
        if x == k[:-1]:
            return v[1]
        if x == int(k[:-1]):
            return v[1]
        if x == str(v[0]):
            return v[1]
        if x == v[1]:
            return v[1]
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

canCHANNELDATA_CHANNEL_CAP = 1
canCHANNELDATA_TRANS_CAP = 2
canCHANNELDATA_CHANNEL_FLAGS = 3
canCHANNELDATA_CARD_TYPE = 4
canCHANNELDATA_CARD_NUMBER = 5
canCHANNELDATA_CHAN_NO_ON_CARD = 6
canCHANNELDATA_CARD_SERIAL_NO = 7
canCHANNELDATA_TRANS_SERIAL_NO = 8
canCHANNELDATA_CARD_FIRMWARE_REV = 9
canCHANNELDATA_CARD_HARDWARE_REV = 10
canCHANNELDATA_CARD_UPC_NO = 11
canCHANNELDATA_TRANS_UPC_NO = 12
canCHANNELDATA_CHANNEL_NAME = 13
canCHANNELDATA_DLL_FILE_VERSION = 14
canCHANNELDATA_DLL_PRODUCT_VERSION = 15
canCHANNELDATA_DLL_FILETYPE = 16
canCHANNELDATA_TRANS_TYPE = 17
canCHANNELDATA_DEVICE_PHYSICAL_POSITION = 18
canCHANNELDATA_UI_NUMBER = 19
canCHANNELDATA_TIMESYNC_ENABLED = 20
canCHANNELDATA_DRIVER_FILE_VERSION = 21
canCHANNELDATA_DRIVER_PRODUCT_VERSION = 22
canCHANNELDATA_MFGNAME_UNICODE = 23
canCHANNELDATA_MFGNAME_ASCII = 24
canCHANNELDATA_DEVDESCR_UNICODE = 25
canCHANNELDATA_DEVDESCR_ASCII = 26
canCHANNELDATA_DRIVER_NAME = 27

class KvaserException(Exception):
    pass

canlib = None
if sys.platform == 'linux2':
    canlib = ctypes.CDLL('libcanlib.so')
    def gettime_linux(handle):
        time = ctypes.c_uint()
        canlib.canReadTimer(handle, ctypes.byref(time))
        return time.value / 1000.0
    canReadTimer = canlib.canReadTimer
elif sys.platform == 'cygwin':
    canlib = ctypes.CDLL('canlib32.dll')
    def gettime_windows(handle):
        x = canlib.canReadTimer(handle)
        return x / 1000.0
    canReadTimer = canlib.kvReadTimer
elif sys.platform == 'win32':
    canlib = ctypes.windll.canlib32
    def gettime_windows(handle):
        x = canlib.canReadTimer(handle)
        return x / 1000.0
    canReadTimer = canlib.kvReadTimer
else:
    s = 'Unknown platform: {0:s}'.format(sys.platform)
    raise KvaserException(s)

def list_channels():
    '''Return a list of connected channels'''
    if not canlib:
        return ()
    canlib.canInitializeLibrary()
    cnt = ctypes.c_int()
    stat = canlib.canGetNumberOfChannels(ctypes.byref(cnt))
    if stat < 0:
        raise KvaserException('canGetNumberOfChannels')
    if (cnt.value < 0) or (cnt.value > 64):
        raise KvaserException('strange number of channels %d' % cnt.value)
    channels = []
    for i in range(cnt.value):
        name = ctypes.create_string_buffer(256)
        stat = canlib.canGetChannelData(i, canCHANNELDATA_CHANNEL_NAME,
                ctypes.byref(name), len(name))
        if stat < 0:
            stat = canlib.canGetChannelData(i, canCHANNELDATA_DEVDESCR_ASCII,
                    ctypes.byref(name), len(name))
            if stat < 0:
                raise KvaserException('canGetChannelData')
        channels.append(name.value)
    return tuple(channels)

class KvaserCanChannel(canchannel.CanChannel):
    def __init__(self, channel=0, bitrate=canBITRATE_125K, silent=False, **kwargs):
        canlib.canInitializeLibrary()
        self.channel = ctypes.c_int(channel)
        br = bitrate_search(bitrate)
        if br is None:
            s = 'Unknown bitrate: {0}'.format(str(bitrate))
            raise KvaserException(s)
        bitrate = br
        self.bitrate = ctypes.c_int(bitrate)
        self.silent = silent
        self.flags = ctypes.c_int(canWANT_EXTENDED | canOPEN_ACCEPT_VIRTUAL)
        self.handle = canlib.canOpenChannel(self.channel, self.flags)
        if self.handle < 0:
            s = ctypes.create_string_buffer(128)
            canlib.canGetErrorText(self.handle, s, 128)
            fmt = 'canOpenChannel(%d, 0x%X=%d: %s'
            txt = fmt % (channel, self.flags.value, self.handle, s.value)
            raise KvaserException(txt)
        res = canlib.canSetBusParams(self.handle
                , *bitrate_settings[bitrate])
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canSetBusParams=%d: %s' % (res, s.value))
        res = canlib.canBusOn(self.handle)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canBusOn=%d: %s' % (res, s.value))
        if self.silent:
            res = canlib.canSetBusOutputControl(self.handle
                    , canDRIVER_SILENT)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                canlib.canGetErrorText(res, s, 128)
                fmt = 'canSetBusOutputControl=%d: %s'
                raise KvaserException(fmt % (res, s.value))
        else:
            res = canlib.canSetBusOutputControl(self.handle
                    , canDRIVER_NORMAL)
            if res != canOK:
                s = ctypes.create_string_buffer(128)
                canlib.canGetErrorText(res, s, 128)
                fmt = 'canSetBusOutputControl=%d: %s'
                raise KvaserException(fmt % (res, s.value))
        super(KvaserCanChannel, self).__init__(**kwargs)

    def gettime(self):
        time = ctypes.c_uint()
        canReadTimer(self.handle, ctypes.byref(time))
        return time.value / 1000.0

    def set_baud(self, handle, baud):
        settings = bitrate_settings[baud]
        res = canlib.canSetBusParams(handle, *settings)
        if res != canOK:
            s = ctypes.create_string_buffer(128)
            canlib.canGetErrorText(res, s, 128)
            raise KvaserException('canSetBusParams=%d: %s' % (res, s.value))

    def __del__(self):
        if canlib != None:
            canlib.canClose(self.handle)

    def do_read(self):
        id = ctypes.c_int()
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_int()
        flags = ctypes.c_int()
        T = ctypes.c_uint()
        res = canlib.canRead(self.handle, ctypes.byref(id), data
                , ctypes.byref(dlc), ctypes.byref(flags), ctypes.byref(T))
        if res == canOK:
            t = T.value / 1000.0
            if flags.value & canMSG_ERROR_FRAME:
                m = canmsg.CanMsg(error_frame=True)
                return m
            d = [ord(data[i]) for i in range(dlc.value)]
            if flags.value & canMSG_EXT != 0:
                ext = True
            else:
                ext = False
            msg = canmsg.CanMsg(can_id=id.value, data=d, extended=ext, time=t
                    , channel=self)
            return msg
        if res != canERR_NOMSG:
            s = ctypes.create_string_buffer(128)
            canlib.canGetErrorText(res, s, 128)
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
            res = canlib.canWrite(self.handle, msg.can_id, d, len(d), flags)
            if res == 0:
                msg.time = self.gettime()
                break
            if cnt % 10 == 0:
                #self.info(5, 'written {0} times'.format(cnt))
                pass
            elif cnt > 10000:
                raise KvaserException('do_write failed(%d)' % res)

class KvaserOptions(optparse.OptionParser):
    def __init__(self):
        optparse.OptionParser.__init__(self)
        def bitrate_callback(option, optstr, value, parser):
            setattr(parser.values, option.dest, bitrate_search(value))
            if parser.values.bitrate == None:
                fmt = 'unknown bitrate <%s>'
                raise canchannel.optparse.OptionValueError(fmt % value)
        self.add_option(
                '-c', '--channel',
                dest='channel', type='int', default=0,
                help='desired channel',
                metavar='CHANNEL')
        x = [str(y[0]) for y in bitrates.values()]
        self.add_option(
                '-b', '--bitrate',
                dest='bitrate', type='string', default=canBITRATE_125K,
                action='callback', callback=bitrate_callback,
                help='desired bitrate (%s)' % ', '.join(x),
                metavar='BITRATE')
        self.add_option(
                '-s', '--silent',
                action='store_true', dest='silent', default=False,
                help='do not talk on the CAN bus',
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
                time.sleep(0.4)
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
                    m.can_id = 0x3F0
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

