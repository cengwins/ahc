#TODO: Remove from AHC, does not use AHC!
import time
from threading import Thread

import matplotlib.pyplot as plt
import networkx as nx

from ahc.SelfStabilization.RWLock import *

class SharedMemoryNode:
  def __init__(self, topology, node_index, K):
    self.topology = topology
    self.node_index = node_index
    self.K = K

    self.thread = None

    self.neighbors = []

    for u, v in list(topology.G.edges):
      if v == self.node_index:
        self.neighbors.append(u)
      elif u == self.node_index:
        self.neighbors.append(v)

    self.parent_node = RWLockedVal(None)
    self.root_node = RWLockedVal(node_index)
    self.distance_to_root = RWLockedVal(0)

  def setup(self):
    pass

  def thread_handler(self):
    raise NotImplementedError(f'method thread_handler is not implemented for {self.__class__.__name__}')

  def start(self):
    self.thread = Thread(target=self.thread_handler)
    self.thread.start()

  def __str__(self):
    return f'{self.__class__.__name__}: {self.node_index}'

  def __repr__(self):
    return self.__str__()


class SharedMemoryTopology:
  def __init__(self):
    self.G = None
    self.node_count = None

    self.nodes = dict()
    self.stable_statuses = dict()

    self.stable = RWLockedVal(False)

  def construct_from_tree(self, G, NodeClass, args=[]):
    self.G = G
    self.node_count = len(list(G.nodes))

    for i in list(G.nodes):
      self.nodes[i] = NodeClass(self, i, *args)
      self.stable_statuses[i] = RWLockedVal(False)

    for i in list(G.nodes):
      self.nodes[i].setup()

  def plot_base_graph(self): # unused function
    nx.draw(self.G, nx.drawing.spring_layout(self.G), node_color=(['b'] * self.node_count), with_labels=True, font_weight='bold')
    plt.draw()

  def plot_directed_graph(self):
    directed_graph = nx.DiGraph()

    directed_graph.add_nodes_from(self.G.nodes)

    for node in self.nodes.values():
      if node.parent_node.val is not None:
        directed_graph.add_edge(node.node_index, node.parent_node.val)

    nx.draw(directed_graph, nx.drawing.spring_layout(directed_graph), node_color=(['b'] * self.node_count), with_labels=True, font_weight='bold')
    plt.draw()

  def stable_check_handler(self):
    while True:
      stable = True

      for locked_v in self.stable_statuses.values():
        if not locked_v.val:
          stable = False
          break

      if stable:
        self.stable.set(True)
        break

      time.sleep(0.0001)

  def start(self):
    for node in self.nodes.values():
      node.start()

    # stable_check_thread = Thread(target=self.stable_check_handler)
    # stable_check_thread.start()
    self.stable_check_handler()

  def plot(self):
    self.plot_directed_graph()
