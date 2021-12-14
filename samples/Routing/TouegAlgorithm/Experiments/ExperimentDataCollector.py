from Ahc import Lock, Thread
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
class ExperimentCollector:
    MESSAGE_COUNT = {}
    network_graph = None
    COMPLETION = {}
    route_table = None
    def getMessageCounts(self):
        return self.MESSAGE_COUNT
    def getNetworkGraph(self):
        return self.network_graph

    def storeResult(self):
        files = [a for a in os.listdir("Results") if ".exp"]
        pickle.dump((self.network_graph, self.MESSAGE_COUNT, self.COMPLETION, self.route_table), open("Results/"+str(timer())+".exp", "wb"))

