import os
import sys
import time

sys.path.insert(0, os.getcwd())

from PhysicalLayers.Channels import Channel
from WaveAlgorithms.EchoAlgorithm import *

def main():

  G = nx.random_geometric_graph(80, 0.5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()

  topo = Topology()
  topo.construct_from_graph(G, EchoNode, Channel)
  # topo.start()
  # time.sleep(3)
  start = time.time()
  startEchoAlgorithm(topo)
  print(f"Start Time: {start}")
  plt.show() 
  while (True): pass

if __name__ == "__main__":
  main()