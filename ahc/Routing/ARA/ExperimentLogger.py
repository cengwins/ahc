import os
import pickle
from timeit import default_timer as timer

def singleton(cls):
  instance = [None]
  def wrapper(*args, **kwargs):
    if instance[0] is None:
      instance[0] = cls(*args, **kwargs)
    return instance[0]
  return wrapper

@singleton
class ExperimentLogger:
  finished = False
  start_time = None
  finish_time = None
  total_hops = 0

  def __init__(self):
    print("Logger Created!")

  # setters
  def set_finished(self):
    self.finished = True
    print("Total route finding time: ", ExperimentLogger().get_time_elapsed())
    print("Total hops for route finding: ", ExperimentLogger().get_total_hops())
    self.storeResult()

  def set_start_time(self, s_time):
    self.start_time = s_time

  def set_finish_time(self, f_time):
    self.finish_time = f_time

  def set_total_hops(self, hops):
    self.total_hops = hops

  # getters
  def get_finished(self):
    return self.finished
  
  def get_time_elapsed(self):
    return self.finish_time - self.start_time

  def get_total_hops(self):
    return self.total_hops

  def storeResult(self):
    elapsed_time = self.finish_time - self.start_time 
    with open(os.getcwd()+".30_"+str(timer())+".exp", "wb") as handle:
      pickle.dump((10, elapsed_time, self.total_hops), handle, protocol=pickle.HIGHEST_PROTOCOL)

