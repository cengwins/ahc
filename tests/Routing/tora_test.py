import os
import sys

sys.path.insert(0, os.getcwd())

import matplotlib.pyplot as plt
import networkx as nx
from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

from Routing.TORA.tora import Height, TORANode


def main():
    G = nx.Graph()
    G.add_nodes_from([0, 7])
    G.add_edge(0, 1)
    G.add_edge(0, 2)
    G.add_edge(0, 3)
    G.add_edge(1, 4)
    G.add_edge(1, 3)
    G.add_edge(2, 6)
    G.add_edge(3, 6)
    G.add_edge(4, 5)
    G.add_edge(5, 7)
    G.add_edge(6, 7)

    nx.draw(G, with_labels=True, font_weight="bold")
    plt.draw()

    topo = Topology()
    topo.construct_from_graph(G, TORANode, P2PFIFOPerfectChannel)
    topo.start()

    destination_id = 5
    source_id = 2

    destination_height: Height = Height(0, 0, 0, 0, destination_id)
    topo.nodes[destination_id].set_height(destination_height)

    topo.nodes[source_id].init_route_creation(destination_id)

    plt.show()

    while True:
        pass


if __name__ == "__main__":
    main()
