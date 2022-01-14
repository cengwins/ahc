import os
import sys

sys.path.insert(0, os.getcwd())

import matplotlib.pyplot as plt

from SelfStabilization.AroraGouda import *
from SelfStabilization.AfekKuttenYang import *


def main():
  G = nx.random_geometric_graph(7, 0.8)

  topology = SharedMemoryTopology()
  topology.construct_from_tree(G, AroraGoudaNode, args=[len(G.nodes)]) # K value

  topology.plot_base_graph()
  plt.show()

  plt.clf()

  topology.start()
  topology.plot()

  plt.show()

if __name__ == "__main__":
  main()
