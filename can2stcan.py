#!/usr/bin/env python
import sys
import stcan
import canmsg

def main():
    for L in sys.stdin:
        #m = canmsg.CanMsg.from_str(L)
        m = stcan.StCanMsg.from_str(L)
        sys.stdout.write(str(m) + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
