import os
import sys

sys.path.insert(0, os.getcwd())

from Ahc import Topology
from widemouthfrog import Node


def main():
  topo = Topology()
  topo.construct_single_node(Node, 0)
  topo.start()
  while True: pass

if __name__ == "__main__":
  main()