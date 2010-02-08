#!/usr/bin/env python
import os
import sys
import exceptions
import serial
import time
import getopt
import canchannel
import canmsg
import vbg_dle

EOF = -1

optionparser = canchannel.optionparser
optionparser.add_option(
        '-b', '--baudrate',
        dest='baudrate',
        help='set the desired baudrate',
        metavar='BAUDRATE',
        type='int',
        default=38400)
optionparser.add_option(
        '-p', '--port',
        dest='port',
        help='where PORT is for example COM1',
        metavar='PORT',
        default='/dev/ttyS4')
optionparser.add_option(
        '--parity',
        dest='parity',
        help='where PARITY is one of N, E, O; i.e. None, Even, Odd',
        metavar='PARITY',
        default='E')
optionparser.add_option(
        '--stopbits',
        dest='stopbits',
        help='number of stop bits',
        metavar='STOPBITS',
        type='int',
        default=1)

def dump_error(s):
    sys.stdout.write(s + '\n')

class SerialCOM(object):
    def __init__(self, portstr='', baud=9600, parity='N', stopbits=1):
        try:
            self.port = serial.Serial(portstr, baudrate=baud, parity=parity, stopbits=stopbits, timeout=0.01)
            if not self.port:
                raise 'Unable to open port \'%s\'' % portstr
        except Exception, e:
            self.port = None
            raise
        self.port.setRTS()

    def open(self):
        self.port.open()

    def close(self):
        if self.port != None:
            self.port.close()

    def __del__(self):
        self.close()

    def read(self):
        c = self.port.read(1)
        if c:
            return ord(c)
        return EOF

    def write(self, b):
        if type(b) is list:
            for ab in b:
                self.port.write(chr(ab & 0xFF))
        else:
            self.port.write(chr(b & 0xFF))

class SerialCanChannel(canchannel.CanChannel):
    def __init__(self, options):
        canchannel.CanChannel.__init__(self, options)
        self.open()

    def open(self):
        canchannel.CanChannel.open(self)
        o = self.options
        self.port = SerialCOM(portstr=o.port,
                baud=o.baudrate,
                parity=o.parity,
                stopbits=o.stopbits)
        self.translator = vbg_dle.DLEHandler(self.port)

    def do_read(self):
        msg = self.translator.read()
        if msg:
            msg.time = self.gettime() - self.starttime
        return msg

    def do_write(self, msg):
        self.translator.write(msg)
        msg.time = self.gettime() - self.starttime

def main():
    canchannel.main(SerialCanChannel)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

