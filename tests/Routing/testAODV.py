import os
import sys
import random

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, ComponentRegistry
from Broadcasting.Broadcasting import ControlledFlooding
from Channels.Channels import P2PFIFOFairLossChannel, P2PFIFOPerfectChannel, FIFOBroadcastPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from Routing.RoutingAODVComponent.RoutingAODVComponent import AODVNode, AODVChannel

def main():
  #TEST 1
  # edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
  #        (3, 5, {"weight": 1}), (1, 4, {"weight": 1}), (4, 6, {"weight": 1}), (4, 7, {"weight": 1}),
  #        (6, 8, {"weight": 1}), (8, 9, {"weight": 1}), (7, 10, {"weight": 1}), (7, 11, {"weight": 1}),
  #        (11, 13, {"weight": 1}), (2, 12, {"weight": 1}),
  #        (7, 9, {"weight": 1})]

  #TEST 2
  # edges = [(0, 1, {"weight": 1}), (1, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 3, {"weight": 1}), (3, 4, {"weight": 1})]

  #TEST 3
  edges = [
  (7, 4, {"weight": 1}),
  (4, 2, {"weight": 1}),
  (2, 6, {"weight": 1}),
  (6, 8, {"weight": 1}),
  (6, 5, {"weight": 1}),
  (6, 1, {"weight": 1}),
  (8, 5, {"weight": 1}),
  (8, 1, {"weight": 1}),
  (5, 3, {"weight": 1}),
  (5, 0, {"weight": 1}),
  (3, 1, {"weight": 1}),
  (3, 0, {"weight": 1}),
  (0, 9, {"weight": 1}),
  (0, 1, {"weight": 1}),
  (1, 9, {"weight": 1})]

  # undirected graph
  G = nx.Graph()
  G.add_edges_from(edges)
  
  #TEST 4
  # G = nx.random_geometric_graph(10, 0.4)


  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()
  topo = Topology()
  topo.construct_from_graph(G, AODVNode, AODVChannel)
  topo.start()

  plt.show()

  while (True): pass

if __name__ == "__main__":
  main()
