#!/usr/bin/env python

# the project root must be in PYTHONPATH for imports
# $ export PYTHONPATH=$(pwd); python tests/AnonymousNetworks/testItaiRodeh.py

import sys
import threading
from time import sleep

import matplotlib.pyplot as plt
import networkx as nx
from Ahc import Topology
from PhysicalLayer.Channels import P2PFIFOPerfectChannel

from AnonymousNetworks.IEEE1394 import FireWireNode

ACTIVE_NODE_COLOUR = "#98971a"
PASSIVE_NODE_COLOUR = "#7c6f64"
LEADER_NODE_COLOUR = "#d79921"
CONTENDING_NODE_COLOUR = "#b16286"
EDGE_COLOUR = "#3c3836"

FPS = 0.4


def main():
    n = int(sys.argv[1])
    print(f"Creating a tree with size {n}")
    G = nx.random_tree(n)

    update = threading.Event()
    draw_delay = threading.Event()
    plt.ion()
    fig = plt.figure(num=0)

    topology = Topology()
    topology.construct_from_graph(G, FireWireNode, P2PFIFOPerfectChannel)
    topology.start()

    FireWireNode.callback = update
    FireWireNode.draw_delay = draw_delay

    while True:
        update.wait()
        node_colours = list()

        G = Topology().G
        pos = nx.spectral_layout(G, center=(0, 0))

        for nodeID in Topology().nodes:
            node = Topology().nodes[nodeID]

            if node.is_leader:
                node_colours.append(LEADER_NODE_COLOUR)
            elif node.in_root_contention:
                node_colours.append(CONTENDING_NODE_COLOUR)
            elif node.is_terminated:
                node_colours.append(PASSIVE_NODE_COLOUR)
            elif not node.is_terminated:
                node_colours.append(ACTIVE_NODE_COLOUR)

        nx.draw(
            G,
            pos,
            node_color=node_colours,
            edge_color=EDGE_COLOUR,
            with_labels=True,
            font_weight="bold",
        )

        fig.canvas.draw()
        fig.canvas.flush_events()
        fig.clear()
        update.clear()
        draw_delay.set()
        sleep(1.0 / FPS)


if __name__ == "__main__":
    main()
