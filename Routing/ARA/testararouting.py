import os
import sys
import time

from ExperimentLogger import ExperimentLogger

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import Thread, Topology
from Ahc import ComponentRegistry
from Channels.Channels import P2PFIFOPerfectChannel

from ARATestComponent import ARATestComponent

registry = ComponentRegistry()

def main():
  node_count = 30
  G = nx.random_geometric_graph(node_count, 0.5)
  nx.draw(G, with_labels=True, font_weight='bold')

  topo = Topology()
  topo.construct_from_graph(G, ARATestComponent, P2PFIFOPerfectChannel)

  topo.start()
  # plt.show() 

  while (True): pass 

if __name__ == "__main__":
  main()
