#!/usr/bin/env python
import time
import curses
import threading
import sys

class LoggerThread(threading.Thread):
    def __init__(self, logwin, infowin):
        self.logwin = logwin
        self.infowin = infowin
        self._txt = []
        self.lock = threading.Lock()
        self.active = True
        threading.Thread.__init__(self, name='Logger')
        self.start()

    def stop(self):
        self.active = False

    def run(self):
        while self.active:
            time.sleep(0.1)
            t = ''
            self.lock.acquire()
            try:
                if self._txt:
                    t = '\n'.join(self._txt) + '\n'
                    self._txt = []
            finally:
                self.lock.release()
            if t:
                self.logwin.addstr(t)
                self.logwin.refresh()

    def info(self, row, txt):
        self.infowin.addstr(row, 0, txt)
        self.infowin.refresh()

    def log(self, txt):
        self.lock.acquire(True)
        try:
            self._txt.append(txt)
        finally:
            self.lock.release()

class Logger(object):
    def __init__(self, logwin, infowin):
        self.my, self.mx = logwin.getmaxyx()
        self._logsize = 100000
        self.loglines = self._logsize * ['']
        self.curline = 0
        self.logwin = logwin
        self.infowin = infowin

    def stop(self):
        pass

    def save(self, filename):
        f = file(filename, 'w')
        s = '\n'.join(self.loglines[:self.curline])
        f.write(s)
        f.close()
        
    def clear(self):
        self.loglines = self._logsize * ['']
        self.curline = 0
        self.update(0)

    def info(self, row, txt):
        self.infowin.addstr(row, 0, txt)
        self.infowin.noutrefresh()

    def log(self, txt):
        line = self.curline % self._logsize
        self.loglines[line] = txt
        self.curline = self.curline + 1
        
    def home(self):
        L = self.my
        self.update(L)
        return L

    def update(self, showline=0):
        if showline > 0:
            line = showline
        else:
            line = self.curline
        line = line % self._logsize
        start = line - self.my
        if start < 0:
            lines = self.loglines[start:] + self.loglines[:line]
        else:
            lines = self.loglines[start:line]
        s = '\n'.join(lines)
        self.logwin.addstr('\n')
        self.logwin.addstr(0, 0, s)
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
        T = 'T{0.T0:5.1f}'.format(self)
        R = 'R {0.R0:d} {0.Rf:.1f}({0.Rf_max:.1f})'.format(self)
        W = 'W {0.W0:d} {0.Wf:.1f}({0.Wf_max:.1f})'.format(self)
        TOT= 'TOT {0.TOT:d}({0.TOTf:.1f})'.format(self)
        return '{0:<8s} {1:<20s} {2:<20s} {3:<20s}'.format(T, R, W, TOT)

class Interface(object):
    def __init__(self, channel):
        self.channel = channel
        self.pause = False
        self.line = 0
        self.scrolling = False

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
            if c == 'q':
                return True
            if c == 'KEY_DOWN':
                self.scroll(1)
            elif c == 'KEY_NPAGE':
                self.scroll(dy)
            elif c == 'KEY_UP':
                self.scroll(-1)
            elif c == 'KEY_PPAGE':
                self.scroll(-dy)
            elif c == 0x7E: #curses.KEY_HOME:
                self.line = self.logger.home()
                self.scrolling = True
                self.update()
            elif c == 's':
                self.logger.save('dump')
            elif c == 0x1B: #ord('S'):
                self.scrolling = False
                self.line = 0
                self.update()
            elif c == 940: #curses.KEY_CDEL
                self.logger.clear()
                self.line = 0
            elif self.channel.action_handler(c):
                return True
            else:
                self.logger.info(3, '{0:<20}'.format(c))
        return False

    def scroll(self, lines):
        cur = self.logger.curline
        if self.scrolling:
            self.line += lines
            if self.line > cur:
                self.line = 0
                self.scrolling = False
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
        infowin = mainwin.subwin(10, self.mx, self.my - 10, 0)
        self.infowin = infowin
        infowin.hline('-', self.mx)
        infowin.addstr(0, self.mx / 2 - 4, 'Info here')
        infowin.refresh()
        logwin = mainwin.subwin(self.my - 10, self.mx, 0, 0)
        self.logwin = logwin
        logwin.scrollok(True)
        mainwin.keypad(True)
        self.logger = Logger(logwin, infowin)
        self.channel.logger = self.logger
        try:
            logwin.nodelay(True)
            T0 = time.time()
            statistics = Statistics(T0)
            while True:
                if not self.pause:
                    self.channel.read()
                if self.input():
                    break
                T = time.time()
                dT = T - T0
                if dT > 1.01:
                    T0 = T
                    c = self.channel
                    R = c.read_cnt
                    W = c.write_cnt
                    statistics.update(T, R, W)
                    self.logger.info(1, str(statistics))
                    self.update()
        finally:
            self.channel.exit_handler()
            self.logger.stop()

