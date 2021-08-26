import os
import sys
import random
import networkx as nx
import matplotlib.pyplot as plt

sys.path.insert(0, os.getcwd())

from Channels import Channel
from WaveAlgorithms.TreeAlgorithm import *

def main():

  G = nx.random_geometric_graph(190, 0.5)
  MST = nx.minimum_spanning_tree(G)

  nx.draw(MST, with_labels=True, font_weight='bold')
  plt.draw()

  topo = Topology()
  topo.construct_from_graph(MST, TreeNode, Channel)
  # topo.start()
  start = time.time()
  startTreeAlgorithm(topo)
  print(f"Start Time: {start}")


  plt.show()  
  while (True): pass

if __name__ == "__main__":
  main()