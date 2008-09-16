#!/bin/env python
import sys
import pycan

try:
    channel = int(sys.argv[1])
except:
    channel = 0

ch = pycan.CanChannel(channel, flags = pycan.canOPEN_ACCEPT_VIRTUAL)

for i in range(100):
    m = pycan.CanMsg(id=64, msg=[1,2,3,i])
    ch.write(m)

