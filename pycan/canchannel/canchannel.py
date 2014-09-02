import sys
import time
import threading
try:
    #python3
    import queue
except:
    # python2
    import Queue as queue
import random

from pycan.canmsg import canmsg

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
        self.starttime = 0
        self.starttime = self.gettime()
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
    
    def _writer(self):
        try:
            while self.running:
                try:
                    m = self.write_queue.get(True, 1)
                    if self.running:
                        self.do_write(m)
                except queue.Empty:
                    pass
        except Exception as e:
            self.log(str(e) + '\n')
            sys.exit()
        finally:
            self.running = False

    def _reader(self):
        try:
            while self.running:
                m = self.do_read()
                if m and self.running:
                    self.read_queue.put(m)
        except Exception as e:
            self.log(str(e) + '\n')
            sys.exit()
        finally:
            self.running = False

    def _message(self):
        try:
            while self.running:
                try:
                    m = self.msg_handler_queue.get(True, 1)
                    if self.running:
                        self.message_handler(m)
                except queue.Empty:
                    pass
        except Exception as e:
            self.log(str(e) + '\n')
            sys.exit()
        finally:
            self.running = False

    def open(self):
        self.starttime = time.time()

    def close(self):
        self.running = False

    def gettime(self):
        return time.time() - self.starttime

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

def main():
    sys.stdout.write('This is the base CAN channel class.\n')
    sys.stdout.write('Only emulated CAN message input is provided.\n')
    ch = CanChannel()
    try:
        time.sleep(0.1)
        s = raw_input('Use curses interface? [y/n]')
        if s and (s[0] in 'yYjJ'):
            import interface
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

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

