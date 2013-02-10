#!/usr/bin/env python
import sys
import time
import threading
import Queue
import random
import canmsg

class CanChannel(object):
    def __init__(self, **kwargs):
        super(CanChannel, self).__init__(**kwargs)
        self.starttime = time.time()
        self.log_lock = threading.Lock()
        self.logger = None
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
        self.write_queue = Queue.Queue()
        self.read_queue = Queue.Queue()
        self.msg_handler_queue = Queue.Queue()
        self._go()

    def _go(self):
        if not self.running:
            self.running = True
            self.msg_handler_thread.start()
            self.write_thread.start()
            self.read_thread.start()
    
    def _writer(self):
        try:
            self.info(3, 'writer thread started')
            while self.running:
                try:
                    m = self.write_queue.get(True, 1)
                    if self.running:
                        self.do_write(m)
                except Queue.Empty:
                    pass
        except Exception, e:
            self.info(0, str(e) + '\n')
            sys.exit()
        finally:
            self.info(3, 'writer thread exit')

    def _reader(self):
        try:
            self.info(2, 'reader thread started')
            while self.running:
                m = self.do_read()
                if m and self.running:
                    self.read_queue.put(m)
        except Exception, e:
            self.info(0, str(e) + '\n')
            sys.exit()
        finally:
            self.info(2, 'reader thread exit')

    def _message(self):
        try:
            self.info(1, 'message thread started')
            while self.running:
                try:
                    m = self.msg_handler_queue.get(True, 1)
                    if self.running:
                        self.message_handler(m)
                except Queue.Empty:
                    pass
        except Exception, e:
            self.info(0, str(e) + '\n')
            sys.exit()
        finally:
            self.info(1, 'message thread exit')

    def open(self):
        self.starttime = time.time()

    def close(self):
        self.info(4, 'close')
        self.running = False
        self.info(4, 'joining threads')
        self.read_thread.join()
        self.info(5, 'read thread joined')
        self.write_thread.join()
        self.info(5, 'write thread joined')
        self.msg_handler_thread.join()
        self.info(5, 'message thread joined')

    def gettime(self):
        return time.time() - self.starttime

    def do_read(self):
        time.sleep(self._dT)
        self._dT = 0.5 * random.random()
        m = canmsg.CanMsg()
        if random.randint(0,1) == 0:
            m.id = random.randint(0, 2**11 - 1)
        else:
            m.id = random.randint(0, 2**29 - 1)
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
        except Queue.Empty:
            return None

    def write(self, m):
        self.write_cnt += 1
        m.channel = self
        m.sent = True
        m.time = self.gettime()
        self.write_queue.put(m)
        self.msg_handler_queue.put(m)

    def info(self, row, x):
        if self.logger == None:
            self.log(x)
        else:
            self.logger.info(row, x)

    def log(self, x):
        if self.logger == None:
            self.log_lock.acquire()
            sys.stdout.write(str(x))
            sys.stdout.write('\n')
            sys.stdout.flush()
            self.log_lock.release()
        else:
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
    except Exception, e:
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

