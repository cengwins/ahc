#!/usr/bin/env python

# the project root must be in PYTHONPATH for imports
# $ export PYTHONPATH=$(pwd); python tests/AnonymousNetworks/testItaiRodeh.py

import sys
import threading
from math import atan2, cos, radians, sin, sqrt
from time import sleep

import matplotlib.pyplot as plt
import networkx as nx
from Ahc import Topology
from Channels import P2PFIFOPerfectChannel

from AnonymousNetworks.IEEE1394 import FireWireNode


def main():
    n = int(sys.argv[1])
    print(f"Creating a tree with size {n}")
    G = nx.random_tree(n)

    topology = Topology()
    topology.construct_from_graph(G, FireWireNode, P2PFIFOPerfectChannel)

    topology.start()
    topology.plot()
    plt.show()


if __name__ == "__main__":
    main()
