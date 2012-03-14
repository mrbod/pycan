#!/usr/bin/env python
import time
import stcan

def main():
    c = stcan.StCanChannel(0)
    try:
        while True:
            m = c.read()
            if m:
                print m
            else:
                time.sleep(0.010)
    finally:
        c.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

