from contextlib import contextmanager
from threading  import Lock

class RWLock:
  def __init__(self):
    self.w_lock = Lock()
    self.num_r_lock = Lock()
    self.num_r = 0

  def r_acquire(self):
    self.num_r_lock.acquire()
    self.num_r += 1

    if self.num_r == 1:
        self.w_lock.acquire()

    self.num_r_lock.release()

  def r_release(self):
    assert self.num_r > 0 # TODO: remove
    self.num_r_lock.acquire()
    self.num_r -= 1

    if self.num_r == 0:
        self.w_lock.release()

    self.num_r_lock.release()

  @contextmanager
  def r_locked(self):
    try:
      self.r_acquire()
      yield
    finally:
      self.r_release()

  def w_acquire(self):
    self.w_lock.acquire()

  def w_release(self):
    self.w_lock.release()

  @contextmanager
  def w_locked(self):
    try:
      self.w_acquire()
      yield
    finally:
      self.w_release()

class RWLockedVal:
  def __init__(self, initial_val):
    self._val = None
    self._lock = RWLock()

    self.set(initial_val)

  @property
  def val(self):
    with self._lock.r_locked():
      return self._val

  def set(self, val):
    with self._lock.w_locked():
      self._val = val
