import threading

from Ahc import singleton


@singleton
class StatsCounter(object):
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.value += 1

    def get(self):
        with self._lock:
            val = self.value
        return val
