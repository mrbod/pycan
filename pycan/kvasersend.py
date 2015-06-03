#!/usr/bin/env python
import sys
import time
import pycan.kvaser as kvaser
import pycan.canmsg as canmsg

def wait(dt):
    dt -= 0.001
    if dt > 0.0:
        time.sleep(dt - 0.001)

def send_file(channel, f, extended, interval):
    if interval is None:
        for m in canmsg.translate(f, True, extended):
            channel.write(m)
    else:
        for m in canmsg.translate(f, False, extended):
            channel.write(m)
            wait(interval)
    time.sleep(0.1)

def send_message(channel, count, interval, m):
    if count is None:
        channel.write(m)
        while True:
            wait(interval)
            channel.write(m)
    else:
        cnt = 0
        if cnt < count:
            channel.write(m)
            cnt += 1
        while cnt < count:
            wait(interval)
            channel.write(m)
            cnt += 1
    time.sleep(0.1)

def execute(args):
    if not args.pure:
        canmsg.format_set(canmsg.FORMAT_BICAN)
    ch = kvaser.KvaserCanChannel(channel=args.channel, bitrate=args.bitrate)
    if args.filename:
        if args.filename == '-':
            f = sys.stdin
        else:
            f = open(args.filename)
        send_file(ch, f, args.extended, args.interval)
    else:
        m = canmsg.CanMsg()
        m.can_id = args.canid
        m.extended = args.extended
        if len(args.data) > 8:
            raise Exception('More than 8 data bytes given')
        m.data = [int(x, 0) for x in args.data]
        interval = (args.interval is None) and 0.1 or args.interval
        send_message(ch, args.count, interval, m)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--channel', type=int, default=0
            , help='select CAN channel, default=%(default)s')
    p.add_argument('-b', '--bitrate', type=int, default=125000
            , help='select CAN bitrate, default=%(default)s')
    p.add_argument('-p', '--pure', action='store_true'
            , help='do not use the default BiCAN format')
    p.add_argument('-i', '--canid', type=int, default=0
            , help='send message(s) with specified CAN id, default=%(default)s')
    p.add_argument('-e', '--extended', action='store_true'
            , help='send extended message(s)')
    p.add_argument('-d', '--data', nargs='*', default=[]
            , help='send message(s) with specified data, default=%(default)s')
    p.add_argument('-t', '--interval', type=float, default=None
            , help='send message(s) with specified interval')
    p.add_argument('-C', '--count', type=int, default=None
            , help='send COUNT message(s), sends forever if not given')
    p.add_argument('filename', nargs='?'
            , help='file with CAN data to replay, timing from file if not --interval is specified')
    args = p.parse_args()
    try:
        execute(args)
    except KeyboardInterrupt:
        print

if __name__ == '__main__':
    main()

