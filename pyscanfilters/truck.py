#!/bin/env python
import time
import sys
import canmsg

data = [0xF7, 0x00, 0x00, 0x04, 0x00, 0xFF, 0x00, 0xFF]

speed = 0

def inc_speed(channel):
    global speed
    if speed < 255:
        speed += 1
    sys.stdout.write('inc_speed: %d\n' % speed)

def dec_speed(channel):
    global speed
    if speed > 0:
        speed -= 1
    sys.stdout.write('dec_speed: %d\n' % speed)

def send_speed(channel):
    data[1] = 0
    data[2] = speed
    m = canmsg.CanMsg(id=0x18FEF1E8, msg=data, flags=canMSG_EXT)
    channel.write(m)

def foo(channel):
    sys.stdout.write('FOO!\n')

actions = {'s':send_speed, 'i':inc_speed, 'd':dec_speed}

def main():
    parse_uart()

if __name__ == '__main__':
    main()
