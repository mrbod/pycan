#!/usr/bin/env python
import sys
import time
import pycan.kvaser as kvaser
import pycan.canmsg as canmsg

def send_file(channel, f, extended, interval):
    if interval is None:
        for m in canmsg.translate(f, True, extended):
            channel.write(m)
    else:
        for m in canmsg.translate(f, False, extended):
            channel.write(m)
            time.sleep(interval)

def send_message(channel, interval, m):
    while True:
        channel.write(m)
        time.sleep(interval)

def execute(args):
    if not args.pure:
        canmsg.format_set(canmsg.FORMAT_BICAN)
    ch = kvaser.KvaserCanChannel(channel=args.channel, bitrate=args.bitrate)
    if args.filename:
        if args.filename == '-':
            send_file(ch, sys.stdin, args.extended, args.interval)
        else:
            send_file(ch, open(args.filename), args.extended, args.interval)
    else:
        m = canmsg.CanMsg()
        m.can_id = args.canid
        m.extended = args.extended
        m.data = [int(x, 0) for x in args.data]
        interval = (args.interval is None) and 0.1 or args.interval
        send_message(ch, interval, m)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--channel', type=int, default=0
            , help='select CAN channel, default=%(default)s')
    p.add_argument('-b', '--bitrate', type=int, default=125000
            , help='select CAN bitrate, default=%(default)s')
    p.add_argument('-p', '--pure', action='store_true'
            , help='do not use the default BiCAN format')
    p.add_argument('-e', '--extended', action='store_true'
            , help='send extended message(s)')
    p.add_argument('-d', '--data', nargs='*', default=[]
            , help='send message(s) with specified data')
    p.add_argument('-i', '--interval', type=float, default=None
            , help='send message(s) with specified interval')
    p.add_argument('-I', '--canid', type=int, default=0
            , help='send message(s) with specified CAN id')
    p.add_argument('filename', nargs='?'
            , help='file with CAN data to replay, timing from file if not --interval is specified')
    args = p.parse_args()
    try:
        execute(args)
    except KeyboardInterrupt:
        print

if __name__ == '__main__':
    main()

