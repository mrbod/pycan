#!/usr/bin/env python
import stcan

class M2(stcan.StCanChannel):
    def message_handler(self, m):
        self.log(m)

stcan.main(1, 2, 5, M2)

