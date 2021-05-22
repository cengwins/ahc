import os
import sys
import time
import pickle
import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime as dt

from Ahc import Topology
from graph import ERG, Grid, Star
from algorithms import AdHocNode, AHCNodeSimulationStatus
from Channels import P2PFIFOPerfectChannel

def run_dijkstra_scholten_simulation(args):
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

def run_shavit_francez_simulation(args):
    raise NotImplementedError()