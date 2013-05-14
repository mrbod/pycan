#!/usr/bin/env python
import time
import curses
import threading
import sys
import canmsg

INFO_WIN_SIZE = 10

class SlotEntry(object):
    def __init__(self, msg):
        self.msg = msg
        self.cnt = 0
        self.dt = 0.0

    def update(self, msg):
        self.dt = msg.time - self.msg.time
        self.msg = msg
        self.cnt += 1

class CanLogger(object):
    slot_fmt = '{0.dt:7.3f} {0.cnt:06d} {0.msg:70s}\n'

    def __init__(self, logwin, infowin, static):
        self.my, self.mx = logwin.getmaxyx()
        self.messages = []
        self.max_cnt = 100000
        self.id_slots = {}
        self.ids = []
        self.curline = 0
        self.last_printed = -1
        self.logwin = logwin
        self.infowin = infowin
        self.sequencial = not static

    def stop(self):
        pass

    def save(self, filename):
        f = file(filename, 'w')
        try:
            for m in self.messages:
                f.write('{0}\n'.format(m))
        finally:
            f.close()
        
    def clear(self):
        self.messages = []
        self.id_slots = {}
        self.ids = []
        self.curline = 0
        self.last_printed = -1
        self.logwin.clear()
        self.update(0)

    def info(self, row, txt):
        if row > INFO_WIN_SIZE - 3:
            return
        self.infowin.addstr(row + 3, 0, txt)
        self.infowin.noutrefresh()

    def log(self, m):
        self.messages.append(m)
        if len(self.messages) > self.max_cnt:
            self.messages = self.messages[self.max_cnt//10:]
        if self.id_slots.has_key(m.id):
            e = self.id_slots[m.id]
        else:
            e = SlotEntry(m)
            self.id_slots[m.id] = e
            self.ids.append(m.id)
            self.ids.sort()
        e.update(m)
        self.curline = self.curline + 1
        
    def sequencial_toggle(self):
        self.sequencial = not self.sequencial
        self.last_printed = len(self.messages) - self.my
        self.logwin.clear()

    def home(self):
        L = self.my
        self.update(L)
        return L

    def update_sequential(self, showline):
        if showline >= 0:
            if showline != self.last_printed:
                self.last_printed = showline
                start = showline - self.my
                if start < 0:
                    start = 0
                ms = self.messages[start:showline]
                for m in ms:
                    self.logwin.addstr(str(m) + '\n')
        else:
            L = len(self.messages)
            if L - self.last_printed > self.my:
                ms = self.messages[L - self.my:L]
            else:
                ms = self.messages[self.last_printed:L]
            self.last_printed = L
            for m in ms:
                self.logwin.addstr(str(m) + '\n')

    def update_slots(self):
        self.logwin.move(0, 0)
        for id in self.ids:
            if self.id_slots.has_key(id):
                e = self.id_slots[id]
                self.logwin.addstr(self.slot_fmt.format(e))

    def update(self, showline=-1):
        if self.sequencial:
            self.update_sequential(showline)
        else:
            self.update_slots()
        self.logwin.noutrefresh()
        curses.doupdate()

class Statistics(object):
    def __init__(self, T):
        self.T0 = T
        self.Ts = T
        self.R0 = 0
        self.Rf = 0.0
        self.Rf_max = 0.0
        self.W0 = 0
        self.Wf = 0.0
        self.Wf_max = 0.0
        self.TOT = 0
        self.TOTf = 0.0

    def update(self, T, R, W):
        self.T = T - self.Ts
        dT = self.T - self.T0
        self.T0 = self.T
        self.Rf = (R - self.R0) / dT
        if self.Rf > self.Rf_max:
            self.Rf_max = self.Rf
        self.R0 = R
        self.Wf = (W - self.W0) / dT
        if self.Wf > self.Wf_max:
            self.Wf_max = self.Wf
        self.W0 = W
        self.TOT = R + W
        self.TOTf = self.TOT / self.T

    def __str__(self):
        T = 'T{0.T0:>5.1f}'.format(self)
        R = 'R {0.R0:d} {0.Rf:.1f}({0.Rf_max:.1f})'.format(self)
        W = 'W {0.W0:d} {0.Wf:.1f}({0.Wf_max:.1f})'.format(self)
        TOT= 'TOT {0.TOT:d}({0.TOTf:.1f})'.format(self)
        return '{0:<8s} {1:<20s} {2:<20s} {3:<20s}'.format(T, R, W, TOT)

class Interface(object):
    def __init__(self, channel, static=False):
        self.statistics = Statistics(self.time())
        self.channel = channel
        self.line = -1
        self.scrolling = False
        self.static = static
        self.mycmd = {'f':'FORMAT', 'q':'QUIT', 'd':'SAVE', 's':'STATIC_TOGGLE', '[7~': 'KEY_HOME', '[8~':'KEY_END', '[3;3~':'KEY_DC'}

    def run(self):
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass

    def input(self):
        c = self.getkey()
        if c != None:
            my, mx = self.logwin.getmaxyx()
            dy = my - 3
            foo = ''
            while c != None:
                foo = foo + c
                if (ord(c[0]) == 27): #ESC
                    txt = ''
                    x = self.getkey()
                    while x != None:
                        txt = txt + x
                        x = self.getkey()
                    c = self.mycmd.get(txt, '')
                    if c == '':
                        self.logger.info(6, '{0:<40}'.format(list(txt)))
                        pass
                if c == 'QUIT':
                    return True
                elif c == 'KEY_DOWN':
                    self.scroll(1)
                elif c == 'KEY_NPAGE':
                    self.scroll(dy)
                elif c == 'KEY_UP':
                    self.scroll(-1)
                elif c == 'KEY_PPAGE':
                    self.scroll(-dy)
                elif c == 'KEY_END':
                    self.scrolling = False
                    self.line = -1
                    self.update()
                elif c == 'KEY_HOME':
                    self.line = self.logger.home()
                    self.scrolling = True
                    self.update()
                elif c == 'FORMAT':
                    canmsg.format_rotate()
                    self.update()
                elif c == 'STATIC_TOGGLE':
                    self.logger.sequencial_toggle()
                elif c == 'SAVE':
                    self.logger.save('can.log')
                elif c == 'KEY_ESC':
                    self.scrolling = False
                    self.line = -1
                    self.update()
                elif c == 'KEY_DC': #curses.KEY_CDEL
                    self.logger.clear()
                    self.statistics = Statistics(self.time())
                    self.channel.read_cnt = 0
                    self.channel.write_cnt = 0
                    self.line = -1
                elif self.channel.action_handler(c):
                    return True
                c = self.getkey()
        return False

    def time(self):
        return time.time()

    def scroll(self, lines):
        cur = self.logger.curline
        if self.scrolling:
            my, mx = self.logwin.getmaxyx()
            self.line += lines
            if self.line > cur:
                self.line = -1
                self.scrolling = False
            elif self.line < my:
                self.line = my
            self.update()
        elif lines < 0:
            self.line = cur + lines
            self.scrolling = True
            self.update()

    def update(self):
        self.logger.update(self.line)

    def getkey(self):
        try:
            return self.mainwin.getkey()
        except:
            return None

    def _run(self, mainwin):
        self.mainwin = mainwin
        mainwin.nodelay(True)
        self.my, self.mx = mainwin.getmaxyx()
        infowin = mainwin.subwin(INFO_WIN_SIZE, self.mx, self.my - INFO_WIN_SIZE, 0)
        self.infowin = infowin
        infowin.hline('-', self.mx)
        infowin.addstr(0, self.mx / 2 - 4, 'Info here')
        infowin.addstr(2, 0, '[Alt-q]-quit, [Alt-s]-static view, [Alt-d]-write file \'can.log\', [Alt-f]-rotate format')
        infowin.refresh()
        logwin = mainwin.subwin(self.my - INFO_WIN_SIZE, self.mx, 0, 0)
        self.logwin = logwin
        logwin.scrollok(True)
        mainwin.keypad(True)
        mainwin.leaveok(0)
        logwin.leaveok(0)
        infowin.leaveok(0)
        self.logger = CanLogger(logwin, infowin, self.static)
        self.channel.logger = self.logger
        self.channel.action_handler('INIT')
        try:
            logwin.nodelay(True)
            T0 = self.time()
            UT0 = T0
            while True:
                T = self.time()
                cnt = 0
                if self.channel.read():
                    cnt += 1
                    dt = T - UT0
                    if dt > 0.01:
                        UT0 = T
                        self.update()
                if self.input():
                    break
                dT = T - T0
                if dT > 1.01:
                    T0 = T
                    c = self.channel
                    R = c.read_cnt
                    W = c.write_cnt
                    self.statistics.update(T, R, W)
                    self.logger.info(-2, str(self.statistics))
                    self.update()
                elif cnt == 0:
                    time.sleep(0.001)
        finally:
            self.channel.exit_handler()
            self.logger.stop()

