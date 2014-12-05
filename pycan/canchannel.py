import sys
import time
import threading
import random
if sys.version_info.major >= 3:
    import queue
else:
    import Queue as queue

from pycan import canmsg

class DefaultLogger(object):
    def __init__(self):
        self.lock = threading.Lock()

    def log(self, x):
        self.lock.acquire()
        sys.stdout.write(str(x) + '\n')
        sys.stdout.flush()
        self.lock.release()

class CanChannel(object):
    def __init__(self, **kwargs):
        self.logger = kwargs.pop('logger', None)
        if self.logger is None:
            self.logger = DefaultLogger()
        self.starttime = self._gettime()
        self.read_cnt = 0
        self.write_cnt = 0
        self._dT = 0.0
        self.running = False
        self.write_thread = threading.Thread(target=self._writer)
        self.write_thread.daemon = True
        self.read_thread = threading.Thread(target=self._reader)
        self.read_thread.daemon = True
        self.msg_handler_thread = threading.Thread(target=self._message)
        self.msg_handler_thread.daemon = True
        self.write_queue = queue.Queue()
        self.read_queue = queue.Queue()
        self.msg_handler_queue = queue.Queue()
        self._go()

    def _go(self):
        if not self.running:
            self.running = True
            self.msg_handler_thread.start()
            self.write_thread.start()
            self.read_thread.start()
    
    def _thread_logic(self, func):
        try:
            while self.running:
                func()
        except Exception as e:
            self.log(str(e) + '\n')
            sys.exit()
        finally:
            self.running = False

    def _writer(self):
        def logic():
            try:
                m = self.write_queue.get(True, 1)
                if self.running:
                    self.do_write(m)
            except queue.Empty:
                pass
        self._thread_logic(logic)

    def _reader(self):
        def logic():
            m = self.do_read()
            if m and self.running:
                self.read_queue.put(m)
        self._thread_logic(logic)

    def _message(self):
        def logic():
            try:
                m = self.msg_handler_queue.get(True, 1)
                if self.running:
                    self.message_handler(m)
            except queue.Empty:
                pass
        self._thread_logic(logic)

    def open(self):
        self.starttime = self._gettime()

    def close(self):
        self.running = False

    def _gettime(self):
        return time.time()

    def _normalize_time(self, t):
        if t < self.starttime:
            self.starttime = 0.0
        return t - self.starttime

    def gettime(self):
        return self._normalize_time(self._gettime())

    def do_read(self):
        time.sleep(self._dT)
        self._dT = 0.5 * random.random()
        m = canmsg.CanMsg()
        no_extended = True
        if no_extended or (random.randint(0,1) == 0):
            m.can_id = random.randint(0, 2**11 - 1)
        else:
            m.can_id = random.randint(0, 2**29 - 1)
            m.extended = True
        m.time = self.gettime()
        dlc = random.randint(0,8)
        m.data = [random.randint(0, 255) for x in range(dlc)]
        return m

    def do_write(self, m):
        pass

    def read(self):
        try:
            m = self.read_queue.get(False)
            self.read_cnt += 1
            m.channel = self
            self.msg_handler_queue.put(m)
            return m
        except queue.Empty:
            return None

    def write(self, m):
        self.write_cnt += 1
        m.channel = self
        m.sent = True
        m.time = self.gettime()
        self.write_queue.put(m)
        self.msg_handler_queue.put(m)

    def log(self, x):
        self.logger.log(x)

    def action_handler(self, key):
        if key == 'INIT':
            self.open()

    def message_handler(self, m):
        self.log(m)

    def exit_handler(self):
        pass

def run():
    sys.stdout.write('This is the base CAN channel class.\n')
    sys.stdout.write('Only emulated CAN message input is provided.\n')
    ch = CanChannel()
    try:
        time.sleep(0.1)
        try:
            foo = raw_input
        except:
            foo = input
        s = foo('Use curses interface? [y/n]')
        if s and (s[0] in 'yYjJ'):
            from pycan import interface
            i = interface.Interface(ch)
            i.run()
        else:
            ch.open()
            while True:
                m = ch.read()
                if not m:
                    time.sleep(0.5)
    except Exception as e:
        sys.stderr.write(str(e))
        raise
    finally:
        sys.stdout.write('closing channel.\n')
        ch.close()
        sys.stdout.write('channel closed.\n')

def main():
    try:
        run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

