#!/usr/bin/env python
import sys
import stcan

for L in sys.stdin:
    m = stcan.StCanMsg.from_str(L)
    sys.stdout.write(str(m))
    sys.stdout.write('\n')

