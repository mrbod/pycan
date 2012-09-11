#!/bin/env python
import socketcan
import interface
import canmsg

class Channel(socketcan.SocketCanChannel):
    def __init__(self, channel):
        socketcan.SocketCanChannel.__init__(self, channel)

    def action_handler(self, c):
        socketcan.SocketCanChannel.action_handler(self, m)

    def message_handler(self, m):
        socketcan.SocketCanChannel.message_handler(self, m)

if __name__ == '__main__':
    channel = Channel(0)
    interface = interface.Interface(channel)
    interface.run()

