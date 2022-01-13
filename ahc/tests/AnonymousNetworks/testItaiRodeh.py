#!/usr/bin/env python

# the project root must be in PYTHONPATH for imports
# $ export PYTHONPATH=$(pwd); python tests/AnonymousNetworks/testItaiRodeh.py

import sys
import threading
from math import atan2, cos, radians, sin
from time import sleep

import matplotlib.pyplot as plt
import networkx as nx
from ahc.Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

from AnonymousNetworks.ItaiRodeh import ItaiRodehNode, State

ACTIVE_NODE_COLOUR = "#ff0000"
PASSIVE_NODE_COLOUR = "#e0e0e0"
LEADER_NODE_COLOUR = "#ff00ff"
EDGE_COLOUR = "#1a1c20"

FPS = 1


def main():
    n = int(sys.argv[1])
    print(f"Creating a ring with size {n}")
    G = nx.cycle_graph(n)

    plt.ion()
    fig = plt.figure(num=0)

    topology = Topology()
    topology.construct_from_graph(G, ItaiRodehNode, P2PFIFOPerfectChannel)
    topology.start()
    ItaiRodehNode.ring_size = n

    update = threading.Event()
    draw_delay = threading.Event()
    ItaiRodehNode.callback = update
    ItaiRodehNode.draw_delay = draw_delay

    while True:
        update.wait()
        assumed_ids = list()
        node_colours = list()

        G = Topology().G
        pos = nx.circular_layout(G, center=(0, 0))

        for nodeID in Topology().nodes:
            node = Topology().nodes[nodeID]
            G.nodes[nodeID]["id_p"] = node.id_p
            assumed_ids.append(node.id_p)

            if node.state == State.active:
                node_colours.append(ACTIVE_NODE_COLOUR)
            elif node.state == State.passive:
                node_colours.append(PASSIVE_NODE_COLOUR)
            elif node.state == State.leader:
                node_colours.append(LEADER_NODE_COLOUR)

        node_id_label_pos = {}
        for key in pos:
            x, y = pos[key]
            theta = atan2(y, x) + radians(75)
            d = 0.1
            node_id_label_pos[key] = (x + d * cos(theta), y + d * sin(theta))

        node_id_labels = nx.get_node_attributes(G, "id_p")

        nx.draw(
            G,
            pos,
            node_color=node_colours,
            edge_color=EDGE_COLOUR,
            with_labels=False,
            font_weight="bold",
        )

        nx.draw_networkx_labels(G, node_id_label_pos, node_id_labels)

        fig.text(0.2, 0.2, f"Round: {ItaiRodehNode.global_round}")

        fig.canvas.draw()
        fig.canvas.flush_events()
        fig.clear()
        update.clear()
        draw_delay.set()
        sleep(1.0 / FPS)


if __name__ == "__main__":
    main()
