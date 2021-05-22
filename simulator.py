import os
import sys
import time
import pickle
import random
import pandas as pd
import networkx as nx
from enum import Enum
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime as dt
from argparse import ArgumentParser

from graph import ERG, Grid, Star
from algorithms import AdHocNode, AHCNodeSimulationStatus
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Ahc import (ComponentModel, Event, ConnectorTypes, Topology,
                 ComponentRegistry, GenericMessagePayload, GenericMessageHeader,
                 GenericMessage, EventTypes)

parser = ArgumentParser()
parser.add_argument("simulation_ticks", type=int)
parser.add_argument("ms_per_tick", type=int)
parser.add_argument("--node_min_activeness_after_receive", type=int, default=3) # paket aldiktan sonra min bu kadar aktif kal
parser.add_argument("--node_max_activeness_after_receive", type=int, default=5) # paket aldiktan sonra max bu kadar aktif kal
parser.add_argument("--node_activeness_communication_prob", type=float, default=0.5) # alive iken baska nodelara paket gonderme olasiligi
parser.add_argument("--node_initial_activeness_prob", type=float, default=0.5)
parser.add_argument("--node_package_process_per_tick", type=int, default=5)

parser.add_argument("--run_until_termination", action="store_true", default=False)
parser.add_argument("--exit_on_termination", action="store_true", default=False)

parser.add_argument("--passiveness_death_thresh", type=int, default=20)
parser.add_argument("--hard_stop_nodes", action="store_true", default=False)
parser.add_argument("--hard_stop_min_tick", type=int, default=50)
parser.add_argument("--hard_stop_max_tick", type=int, default=300)
parser.add_argument("--hard_stop_prob", type=float, default=0.5)

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

    if args.run_until_termination:
        args.simulation_ticks = 10**10

    assert args.hard_stop_max_tick < args.simulation_ticks
    assert args.hard_stop_min_tick > 0

    hard_stop_on_tick = None

    if args.hard_stop_nodes:
        hard_stop_on_tick = [random.randint(args.hard_stop_min_tick, args.hard_stop_max_tick) for _ in range(total_nodes)]

    node_active_ticks_initial = [random.randint(args.node_min_activeness_after_receive, args.node_max_activeness_after_receive) if random.random() <= args.node_initial_activeness_prob else 0 for _ in range(total_nodes)]
    topo_context = {
        "network": N,
        "ms_per_tick": args.ms_per_tick,
        "simulation_ticks": args.simulation_ticks,
        "initial_liveness": node_active_ticks_initial,
        "communication_on_active_prob": args.node_activeness_communication_prob,
        "min_activeness_after_receive": args.node_min_activeness_after_receive,
        "max_activeness_after_receive": args.node_max_activeness_after_receive,
        "node_package_process_per_tick": args.node_package_process_per_tick,
        "passiveness_death_thresh": args.passiveness_death_thresh,
        "hard_stop_on_tick": hard_stop_on_tick
    }

    print(topo_context)
    # N.plot()
    # plt.show()

    topo = Topology()
    topo.construct_from_graph(N.G, AdHocNode, P2PFIFOPerfectChannel, context=topo_context)

    topo.start()

    stats = {
        "df": pd.DataFrame(data={
            "dead_nodes": [],
            "active_nodes": [],
            "packages_in_transmit": [],
        }),
        "terminated_on_tick": None
    }

    fig, axes = plt.subplots(1, 1)
    fig.set_figwidth(20)
    fig.set_figheight(5)
    # fig.tight_layout()

    input("\n>>> Proceed ?")

    try:
        for t in range(1, args.simulation_ticks + 1):
            print(f"[S] Tick: {t}")

            packages_sent = 0
            packages_waiting_on_queue = 0
            num_nodes_active = 0
            num_dead_nodes = 0

            for node in topo.nodes.values():
                new_state, pkg_sent_to_friend = node.simulation_tick()

                if new_state == AHCNodeSimulationStatus.ACTIVE:
                    num_nodes_active += 1
                elif new_state == AHCNodeSimulationStatus.OUT_OF_CLOCK:
                    num_dead_nodes += 1

                if pkg_sent_to_friend is not None:
                    packages_sent += 1
                
                packages_waiting_on_queue += node.waiting_packages_on_queue

            stats["df"].loc[t-1] = [num_dead_nodes, num_nodes_active, packages_sent]

            # stats["dead_nodes"].append(num_dead_nodes)
            # stats["active_nodes"].append(num_nodes_active)
            # stats["packages_in_transmit"].append(packages_sent)

            print(f"   (ACTIVE: {num_nodes_active}, PKGS-WAIT: {packages_waiting_on_queue}, PKGS-SENT: {packages_sent})")

            if (packages_waiting_on_queue == 0 and num_nodes_active == 0 and packages_sent == 0):
                stats["terminated_on_tick"] = t
                print("!!! TERMINATED !!!")

                if args.exit_on_termination:
                    break

            # axes.scatter(x=t, y=num_nodes_active)
            axes.cla()
            sns.lineplot(data=stats["df"], ax=axes, color="red")
            # sns.lineplot(data=stats["active_nodes"], ax=axes, color="red")
            # sns.lineplot(data=stats["dead_nodes"], ax=axes, color="mediumslateblue")
            # sns.lineplot(data=stats["packages_in_transmit"], ax=axes, color="green")
            plt.pause(0.0005)
            time.sleep(args.ms_per_tick / 1000)
    except KeyboardInterrupt:
        pass

    ts = dt.now().timestamp()

    # axes.cla()
    # sns.lineplot(data=stats["active_nodes"], ax=axes)
    # sns.kdeplot(data=stats["active_nodes"], ax=axes)

    #plt.plot(stats["packages_in_transmit"])

    plt.savefig(f"simdump/stats_{args.network_type}_{total_nodes}_{ts}.png", dpi=200)

    with open(f"simdump/run_{args.network_type}_{total_nodes}_{ts}.pkl", "wb") as fp:
        pickle.dump({
            "args": args,
            "context": topo_context,
            "stats": stats
        }, fp)

    plt.show()

    ## IMPORTANT
    # possibe evaluation metrics
    # num(control packages) / num(total packages) => 
    # tick(algo done) - tick(termination) => ne kadar erken detect etti