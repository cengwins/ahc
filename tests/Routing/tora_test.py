import os
import sys
import time

sys.path.insert(0, os.getcwd())

import matplotlib.pyplot as plt
import networkx as nx

sys.path.insert(0, os.getcwd())

from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

from Routing.TORA.tora import (
    RoutingTORAComponent,
    TORAHeight,
    all_edges,
    heights,
    wait_for_action_to_complete,
)


def main():
    G = nx.random_tree(8)

    nx.draw(G, with_labels=True, font_weight="bold")
    plt.draw()
    plt.show()

    topo = Topology()
    topo.construct_from_graph(G, RoutingTORAComponent, P2PFIFOPerfectChannel)
    destination_id = 7
    source_id = 0
    destination_height: TORAHeight = TORAHeight(0, 0, 0, 0, destination_id)
    topo.start()

    t = time.time()
    topo.nodes[destination_id].set_height(destination_height)
    topo.nodes[source_id].init_route_creation(destination_id)
    print(wait_for_action_to_complete() - t)
    topo.nodes[source_id].send_message(destination_id, "Test message")

    G2 = nx.DiGraph()
    for node, height in heights(topo):
        G2.add_node(node, label=height)
    edges = all_edges(topo)
    G2.add_edges_from(edges)
    print(edges)

    nx.draw(G2, with_labels=True, font_weight="bold", arrows=True)
    plt.draw()
    plt.show()


if __name__ == "__main__":
    main()
