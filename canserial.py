#!/usr/bin/env python
import os
import sys
import serial
import time
import getopt
import canchannel
import canmsg
import interface
import vbg_dle

def dump_error(s):
    sys.stdout.write(s + '\n')

class SerialCOM(object):
    def __init__(self, portstr='/dev/ttyS0', baud=38400):
        self.port = serial.Serial(portstr, baud, parity='E', timeout=0.01)
        self.port.setRTS()

    def __del__(self):
        self.port.close()

    def read(self):
        c = self.port.read(1)
        if c:
            return ord(c)
        return vbg_dle.EOF

    def write(self, b):
        if type(b) is list:
            for ab in b:
                self.port.write(chr(ab & 0xFF))
        else:
            self.port.write(chr(b & 0xFF))

class SerialCanChannel(canchannel.CanChannel):
    def __init__(self, comport='/dev/ttyS0', baudrate=38400, on_msg=None):
        self.port = SerialCOM(comport, baudrate)
        self.dle_handler = vbg_dle.VBGDLEHandler(self.port)
        canchannel.CanChannel.__init__(self, on_msg)

    def frame2can(self, frame):
        id = (frame[0] << 8) + frame[1]
        data = frame[2:-1]
        return canmsg.CanMsg(id=id, data=data)

    def can2frame(self, m):
        frame = []
        frame.append((m.id >> 8) & 0xFF)
        frame.append(m.id & 0xFF)
        frame += m.data
        return frame

    def do_read(self):
        frame = self.dle_handler.read()
        if type(frame) is int:
            if frame == vbg_dle.EOF:
                pass
            elif frame == ERROR_PADDING:
                dump_error('ERROR: PADDING')
            else:
                dump_error('ERROR: decode, unknown status(%d)' % frame)
        elif type(frame) is list:
            if len(frame) < 2:
                dump_error('ERROR: LENGTH')
            else:
                try:
                    m = self.frame2can(frame)
                    m.time = self.gettime() - self.starttime
                    return m
                except Exception, e:
                    dump_error('ERROR: %s' % str(e))
        else:
            dump_error('ERROR: decode, unknown frame type(%s)' % str(type(frame)))
        return None

    def do_write(self, msg):
        self.dle_handler.send(self.can2frame(msg))
        msg.time = self.gettime() - self.starttime

def usage():
    prg_name = os.path.basename(sys.argv[0])
    print 'Usage: %s [options]' % (prg_name,)
    print
    print 'Options:'
    print '\t-p COMX port, i.e. -p COM1'
    print '\t-b baudrate, default 38400'
    print '\t-f FILE, load FILE as config file'

class SerialOptions():
    def __init__(self):
        self.port = ''
        self.baudrate = 38400
        self.actions = None
        self.handler = None

        try:
            opts, args = getopt.getopt(sys.argv[1:], "hp:b:f:")
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
            elif o[0] == '-p':
                self.port = o[1]
            elif o[0] == '-b':
                self.baudrate = int(o[1])
            elif o[0] == '-f':
                filterfile = o[1]

        if self.port == '':
            usage()
            sys.exit(1)

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
                print >>sys.stderr, 'No handler specified'
            try:
                self.actions = filterdict['actions']
            except KeyError, e:
                print >>sys.stderr, 'No actions specified'

def main():
    o = SerialOptions()
    ch = SerialCanChannel(o.port, baudrate=o.baudrate, on_msg=o.handler)
    interface.main(ch, o.actions)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

