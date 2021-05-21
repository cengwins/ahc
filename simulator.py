import os
import sys
import time
import random
import networkx as nx
from enum import Enum
import matplotlib.pyplot as plt
from argparse import ArgumentParser

from graph import ERG, Grid, Star
from algorithms import AdHocNode
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Ahc import (ComponentModel, Event, ConnectorTypes, Topology,
                 ComponentRegistry, GenericMessagePayload, GenericMessageHeader,
                 GenericMessage, EventTypes)

parser = ArgumentParser()
parser.add_argument("simulation_ticks", type=int)
parser.add_argument("ms_per_tick", type=int)
parser.add_argument("--node_min_activeness_after_receive", type=int, default=3)
parser.add_argument("--node_max_activeness_after_receive", type=int, default=10)
parser.add_argument("--node_activeness_communication_prob", type=float, default=0.5)
parser.add_argument("--node_initial_activeness_prob", type=float, default=0.8)

sp = parser.add_subparsers()

erg_parser = sp.add_parser("erg")
erg_parser.add_argument("node_count", type=int)
erg_parser.add_argument("--node_connectivity", type=float, default=0.5)
erg_parser.set_defaults(network_type="erg")

grid_parser = sp.add_parser("grid")
grid_parser.add_argument("node_count_on_edge", type=int)
grid_parser.set_defaults(network_type="grid")

star_parser = sp.add_parser("star")
star_parser.add_argument("slave_count", type=int)
star_parser.add_argument("--master_is_root", type=bool, default=True)
star_parser.set_defaults(network_type="star")

if __name__ == "__main__":
    args = parser.parse_args()
    print(f"[+] Network type: {args.network_type}")

    if args.network_type == "erg":
        N = ERG(args.node_count, args.node_connectivity)
        total_nodes = args.node_count
    elif args.network_type == "grid":
        N = Grid(args.node_count_on_edge)
        total_nodes = args.node_count_on_edge ** 2
    elif args.network_type == "star":
        N = Star(args.slave_count, master_is_root=args.master_is_root)
        total_nodes = args.slave_count + 1

    node_active_ticks_initial = [random.randint(args.node_min_activeness_after_receive, args.node_max_activeness_after_receive) if random.random() <= args.node_initial_activeness_prob else 0 for _ in range(total_nodes)]

    # N.plot()
    # plt.show()

    topo = Topology()
    topo.construct_from_graph(N.G, AdHocNode, P2PFIFOPerfectChannel, context={
        "network": N,
        "ms_per_tick": args.ms_per_tick,
        "simulation_ticks": args.simulation_ticks,
        "initial_liveness": node_active_ticks_initial,
        "communication_on_active_prob": args.node_activeness_communication_prob,
        "min_activeness_after_receive": args.node_min_activeness_after_receive,
        "max_activeness_after_receive": args.node_max_activeness_after_receive,
    })

    topo.start()

    N.plot()
    plt.show()