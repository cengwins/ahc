import os
import sys
import time
import random
from enum import Enum

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels.Channels import P2PFIFOPerfectChannel
from Routing.LabeledDistanceRouting.RoutingLdrComponent import LDRnode

registry = ComponentRegistry()

def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    G = nx.random_geometric_graph(10, 0.5)
    nx.draw(G, with_labels=True, font_weight='bold')
    plt.draw()

    topo = Topology()
    topo.construct_from_graph(G, LDRnode, P2PFIFOPerfectChannel)
    topo.start()

    plt.show()  # while (True): pass   

if __name__ == "__main__":
    main()
