import os
import sys
import time
import pickle
import random
from typing import Text
import pandas as pd
import seaborn as sns
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime as dt
from networkx.drawing.nx_pydot import graphviz_layout

from Ahc import Topology
from graph import ERG, Grid, Star
from shavit_francez import ShavitFrancezAdHocNode, SFAHCNodeSimulationStatus
from Channels import P2PFIFOPerfectChannel

def run_shavit_francez_simulation(args):
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
    alive_nodes = list(range(total_nodes))
    
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
        "hard_stop_on_tick": hard_stop_on_tick,
        "alive_nodes": alive_nodes,
        "only_root_alive_initially": args.only_root_alive_initially
    }

    print(topo_context)
    # N.plot()
    # plt.show()

    topo = Topology()
    topo.construct_from_graph(N.G, ShavitFrancezAdHocNode, P2PFIFOPerfectChannel, context=topo_context)

    topo.start()

    stats = {
        "df": pd.DataFrame(data={
            "dead_nodes": [],
            "active_nodes": [],
            "packets_in_transmit": [],
            "queued_packets": [],
            "control_packets_sent": [],
            "control_basic_instant_ratio": [],
            "control_total_cumulative_ratio": [],
            "wave_packets_sent": [],
            "wave_basic_instant_ratio": [],
            "wave_total_cumulative_ratio": [],
        }),
        "terminated_on_tick": None,
        "announced_on_tick": None
    }

    graphs = []

    fig, axes = plt.subplots(2, 3)
    fig.set_figwidth(25)
    fig.set_figheight(10)
    # fig.tight_layout()

    input("\n>>> Proceed ?")

    term_wait_ctr = 0
    reason = None

    try:
        for t in range(1, args.simulation_ticks + 1):
            print(f"[S] Tick: {t}")

            packages_sent = 0
            packages_waiting_on_queue = 0
            num_nodes_active = 0
            num_dead_nodes = 0
            break_this_tick = False
            control_packets_sent = 0
            wave_packets_sent = 0

            T = nx.Graph()
            node_color = []

            for index, node in topo.nodes.items():
                new_state, pkg_sent_to_friend, cps, wps = node.simulation_tick()

                if N.root == index:
                    node_color.append("red")
                elif new_state == SFAHCNodeSimulationStatus.ACTIVE:
                    node_color.append("green")
                elif new_state == SFAHCNodeSimulationStatus.PASSIVE:
                    node_color.append("mediumslateblue")
                elif new_state == SFAHCNodeSimulationStatus.OUT_OF_TREE:
                    node_color.append("gray")

                if index not in T.nodes():
                    T.add_node(index)

                if node.parent_node is not None:
                    if node.parent_node not in T.nodes():
                        T.add_node(node.parent_node)

                    T.add_edge(index, node.parent_node)

                if index == N.root and new_state is None:
                    reason = f"root terminated ({t})"
                    break_this_tick = True

                if new_state == SFAHCNodeSimulationStatus.ACTIVE:
                    num_nodes_active += 1
                elif new_state == SFAHCNodeSimulationStatus.OUT_OF_TREE:
                    num_dead_nodes += 1

                if pkg_sent_to_friend is not None:
                    packages_sent += 1

                control_packets_sent += cps
                wave_packets_sent += wps
                packages_waiting_on_queue += node.waiting_packages_on_queue

            print(f"   (ACTIVE: {num_nodes_active}, PKGS-WAIT: {packages_waiting_on_queue}, PKGS-SENT: {packages_sent})")

            if (packages_waiting_on_queue == 0 and num_nodes_active == 0 and packages_sent == 0):
                if not args.no_realtime_plot:
                    if stats["terminated_on_tick"] is None: 
                        stats["terminated_on_tick"] = t

                print("!!! TERMINATED !!!")

                term_wait_ctr += 1

                if args.wait_ticks_after_termination > 0 and term_wait_ctr > args.wait_ticks_after_termination:
                    print("!!! FORCE TERMINATED !!!")
                    reason = f"forced ({args.wait_ticks_after_termination})"
                    break_this_tick = True

                if args.exit_on_termination:
                    break_this_tick = True

            total_pkgs_sent_cum = (stats["df"]["control_packets_sent"].sum() + control_packets_sent + stats["df"]["packets_in_transmit"].sum() + packages_sent + stats["df"]["wave_packets_sent"].sum() + wave_packets_sent)

            stats["df"].loc[t-1] = [
                num_dead_nodes,
                num_nodes_active,
                packages_sent,
                packages_waiting_on_queue,
                control_packets_sent,
                (control_packets_sent / packages_sent) if packages_sent > 0 else 0, # TODO: Fix later, find a better soln,,,
                (((stats["df"]["control_packets_sent"].sum() + control_packets_sent) / total_pkgs_sent_cum) if total_pkgs_sent_cum > 0 else 0) * 100,
                wave_packets_sent,
                (wave_packets_sent / packages_sent) if packages_sent > 0 else 0, # TODO: Fix later, find a better soln,,,
                (((stats["df"]["wave_packets_sent"].sum() + wave_packets_sent) / total_pkgs_sent_cum) if total_pkgs_sent_cum > 0 else 0) * 100,
            ]

            # stats["dead_nodes"].append(num_dead_nodes)
            # stats["active_nodes"].append(num_nodes_active)
            # stats["packages_in_transmit"].append(packages_sent)
            graphs.append({
                "edges": T.edges(),
                "nodes": T.nodes(),
            })

            # axes.scatter(x=t, y=num_nodes_active)
            
            if not args.no_realtime_plot:
                axes[0][0].cla()
                axes[0][1].cla()
                axes[0][2].cla()
                axes[1][0].cla()
                axes[1][1].cla()
                axes[1][2].cla()

                sns.lineplot(data=stats["df"]["active_nodes"], ax=axes[0][0], color="orange")
                sns.lineplot(data=stats["df"]["dead_nodes"], ax=axes[0][0], color="blue")
                sns.lineplot(data=stats["df"]["packets_in_transmit"], ax=axes[0][1], color="purple")
                sns.lineplot(data=stats["df"]["control_packets_sent"], ax=axes[0][1], color="green")
                sns.lineplot(data=stats["df"]["wave_packets_sent"], ax=axes[0][1], color="blue")
                sns.lineplot(data=stats["df"]["control_total_cumulative_ratio"], ax=axes[1][0], color="mediumslateblue")
                sns.lineplot(data=stats["df"]["wave_total_cumulative_ratio"], ax=axes[1][0], color="yellow")
                sns.lineplot(data=stats["df"]["control_basic_instant_ratio"], ax=axes[1][1], color="red")
                sns.lineplot(data=stats["df"]["wave_basic_instant_ratio"], ax=axes[1][1], color="orange")
                # sns.lineplot(data=stats["active_nodes"], ax=axes, color="red")
                # sns.lineplot(data=stats["dead_nodes"], ax=axes, color="mediumslateblue")
                # sns.lineplot(data=stats["packages_in_transmit"], ax=axes, color="green")

                # pos = nx.spring_layout(T)
                # nx.draw_networkx_nodes(T , pos, nodelist=[N.root], node_color='red', ax=axes[0][2])
                # nx.draw_networkx_nodes(T , pos, nodelist=[i for i in T.nodes() if i != N.root], node_color='mediumslateblue', ax=axes[0][2])
                # nx.draw_networkx_edges(T , pos, ax=axes[0][2])

                # pos = graphviz_layout(T, prog="twopi")
                # nx.draw(T, ax=axes[0][2], pos=pos)

                # node_color = ["red" if list(T.nodes)[i] == N.root else ("mediumslateblue" if list(T.nodes)[i] not in alive_nodes else "green") for i in range(total_nodes)]
                nx.draw(T, ax=axes[0][2], with_labels=True, node_color=node_color)
                
                if args.network_type == "grid":   
                    pos = {i: (i // args.node_count_on_edge, i % args.node_count_on_edge) for i in range(total_nodes)}
                    nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color, pos=pos)
                else:
                    nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color)

                plt.pause(0.0005)

            if break_this_tick:
                break

            time.sleep(args.ms_per_tick / 1000)
    except KeyboardInterrupt:
        pass

    ts = dt.now().timestamp()

    # axes.cla()
    # sns.lineplot(data=stats["active_nodes"], ax=axes)
    # sns.kdeplot(data=stats["active_nodes"], ax=axes)

    #plt.plot(stats["packages_in_transmit"])

    axes[0][0].cla()
    axes[0][1].cla()
    axes[0][2].cla()
    axes[1][0].cla()
    axes[1][1].cla()
    axes[1][2].cla()

    sns.lineplot(data=stats["df"]["active_nodes"], ax=axes[0][0], color="orange")
    sns.lineplot(data=stats["df"]["dead_nodes"], ax=axes[0][0], color="blue")
    sns.lineplot(data=stats["df"]["packets_in_transmit"], ax=axes[0][1], color="purple")
    sns.lineplot(data=stats["df"]["control_packets_sent"], ax=axes[0][1], color="green")
    sns.lineplot(data=stats["df"]["control_total_cumulative_ratio"], ax=axes[1][0], color="mediumslateblue")
    sns.lineplot(data=stats["df"]["control_basic_instant_ratio"], ax=axes[1][1], color="red")
    
    nx.draw(T, ax=axes[0][2], with_labels=True, node_color=node_color)
    
    if args.network_type == "grid":   
        pos = {i: (i // args.node_count_on_edge, i % args.node_count_on_edge) for i in range(total_nodes)}
        nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color, pos=pos)
    else:
        nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color)

    plt.savefig(f"simdump/SF_stats_{args.network_type}_{total_nodes}_{ts}.png", dpi=200)

    with open(f"simdump/SF_run_{args.network_type}_{total_nodes}_{ts}.pkl", "wb") as fp:
        pickle.dump({
            "args": args,
            "context": topo_context,
            "stats": stats,
            "graphs": graphs
        }, fp)

    if not args.no_realtime_plot:
        plt.show()

    print(f"\n{reason}")
