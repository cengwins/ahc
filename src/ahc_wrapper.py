import queue
from typing import ClassVar
from helpers import *
from generics import *
from definitions import *
from topology import *
from threading import Thread, Lock
from random import sample
from OSIModel import *
import networkx as nx
class ahc_wrapper:

  component_model = ComponentModel()
  topology = Topology()
  graph= None

  
  def __init__(self, g: nx.Graph):
      self.graph = g

  def create_topology_by_graph(self, g: nx.Graph, nodetype, channeltype, context=None):
    self.topology.construct_from_graph(g, nodetype, channeltype, context)

  def create_network_by_topology(self, t: Topology):
    self.topology = t

  def set_base_model(self, model):
    self.component_model = model

  def create_osi_network(self):
    self.layer_order = LayerOrder()
    pass

  def create_custom_network(self, layers: LayerOrder = LayerOrder):
    pass

class Topology: 

