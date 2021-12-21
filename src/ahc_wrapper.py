import queue
from typing import ClassVar
from helpers import *
from generics import *
from definitions import *
from topology import *
from enum import Enum
from threading import Thread, Lock
from random import sample
import networkx as nx

inf = float('inf')

class ahc_wrapper:

  component_model = ComponentModel
  topology = None

  
  def __init__(self, g: nx.Graph):
      self.graph = g

  def create_topology_by_graph(self, g: nx.Graph):
    pass

  def create_network_by_topology(self, t: Topology):
    self.topology = t

  def set_base_model(self, model):
    self.component_model = model

  def create_network(self):
    pass

  
