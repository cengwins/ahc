from typing import List
import networkx as nx

from helpers import *
from generics import *
from definitions import *

import GenericLinkLayer
import GenericApplicationLayer
import GenericNetworkLayer

class AdHocNode:

  neighbors: List[int] = []
  node_id : int = 0


  def __init__(self, componentname, componentId):

    self.node_id = componentId
    self.component_name = componentname

    self.appllayer = GenericApplicationLayer("ApplicationLayer", self.node_id)
    self.netlayer = GenericNetworkLayer("NetworkLayer", self.node_id)      
    self.linklayer = GenericLinkLayer("LinkLayer", self.node_id) 
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)

  def get_neighbours(self, graph: nx.Graph, calculate_from_graph=False):
      pass
  