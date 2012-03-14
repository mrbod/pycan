#!/bin/env python
import socketcan
import interface

if __name__ == '__main__':
    channel = socketcan.SocketCanChannel(0)
    interface = interface.Interface(channel)
    interface.run()

