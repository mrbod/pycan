import sys
import time
import threading

class Logger(object):
    def __init__(self, output=None):
        if output == None:
            self.output = sys.stdout
        else:
            self.output = output
        self.active = True
        self._txt = []
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, name='Logger')
        self.thread.start()

    def _run(self):
        while self.active:
            time.sleep(0.1)
            t = ''
            self._lock.acquire()
            try:
                if self._txt:
                    t = '\n'.join(self._txt) + '\n'
                    self._txt = []
            finally:
                self._lock.release()
            if t:
                self.output.write(t)
                self.output.flush()

    def log(self, txt):
        self._lock.acquire(True)
        try:
            self._txt.append(txt)
        finally:
            self._lock.release()

