import os
import time
import pickle
import random
import pandas as pd
import seaborn as sns
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime as dt

from ahc.Ahc import Topology
from graph import ERG, Grid, Star
from ahc.TerminationDetection.dijkstra_scholten import DijkstraScholtenAdHocNode, DSAHCNodeSimulationStatus
from ahc.Channels.Channels import P2PFIFOPerfectChannel

import glob
from PIL import Image

# # filepaths
# fp_in = "/path/to/image_*.png"
# fp_out = "/path/to/image.gif"

def make_gif(from_path: str, to_path: str, out_file: str, duration: int) -> None:
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
    _images = sorted(glob.glob(from_path))
    print(_images)
    img, *imgs = [Image.open(f) for f in _images]
    img.save(fp=f"{to_path}/{out_file}", format='GIF', append_images=imgs,
            save_all=True, duration=duration, loop=0)

def run_dijkstra_scholten_simulation(args):
    ts = dt.now().timestamp()

    if args.network_type == "erg":
        N = ERG(args.node_count, args.node_connectivity)
        total_nodes = args.node_count
    elif args.network_type == "grid":
        N = Grid(args.node_count_on_edge)
        total_nodes = args.node_count_on_edge ** 2
    elif args.network_type == "star":
        N = Star(args.slave_count, master_is_root=args.master_is_root)
        total_nodes = args.slave_count + 1

    if args.save_tick_plots:
        tick_plots_save_path = f"{args.tick_plots_save_dir}/DS_{args.network_type}_{total_nodes}_{ts}/"
        os.mkdir(tick_plots_save_path)

        print(f"++ Tick plots will be saved to: {tick_plots_save_path}")

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

    topo = Topology()
    topo.construct_from_graph(N.G, DijkstraScholtenAdHocNode, P2PFIFOPerfectChannel, context=topo_context)

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

            T = nx.Graph()
            node_color = []

            for index, node in topo.nodes.items():
                new_state, pkg_sent_to_friend, cps = node.simulation_tick()

                if N.root == index:
                    node_color.append("red")
                elif new_state == DSAHCNodeSimulationStatus.ACTIVE:
                    node_color.append("green")
                elif new_state == DSAHCNodeSimulationStatus.PASSIVE:
                    node_color.append("mediumslateblue")
                elif new_state == DSAHCNodeSimulationStatus.OUT_OF_TREE:
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

                if new_state == DSAHCNodeSimulationStatus.ACTIVE:
                    num_nodes_active += 1
                elif new_state == DSAHCNodeSimulationStatus.OUT_OF_TREE:
                    num_dead_nodes += 1

                if pkg_sent_to_friend is not None:
                    packages_sent += 1

                control_packets_sent += cps
                packages_waiting_on_queue += node.waiting_packages_on_queue

            print(f"   (ACTIVE: {num_nodes_active}, PKGS-WAIT: {packages_waiting_on_queue}, PKGS-SENT: {packages_sent})")

            if (packages_waiting_on_queue == 0 and num_nodes_active == 0 and packages_sent == 0):
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

            total_pkgs_sent_cum = (stats["df"]["control_packets_sent"].sum() + control_packets_sent + stats["df"]["packets_in_transmit"].sum() + packages_sent)

            stats["df"].loc[t-1] = [
                num_dead_nodes,
                num_nodes_active,
                packages_sent,
                packages_waiting_on_queue,
                control_packets_sent,
                (control_packets_sent / packages_sent) if packages_sent > 0 else 0, # TODO: Fix later, find a better soln,,,
                (((stats["df"]["control_packets_sent"].sum() + control_packets_sent) / total_pkgs_sent_cum) if total_pkgs_sent_cum > 0 else 0) * 100
            ]

            graphs.append({
                "edges": T.edges(),
                "nodes": T.nodes(),
            })
            
            if not args.no_realtime_plot or args.save_tick_plots:
                axes[0][0].cla()
                axes[0][1].cla()
                axes[0][2].cla()
                axes[1][0].cla()
                axes[1][1].cla()
                axes[1][2].cla()

                axes[0][0].set_title("Active/Dead Nodes")
                axes[0][0].set_xlabel(f"Simulation Ticks ({args.ms_per_tick}ms/tick)")
                axes[0][0].set_ylabel(f"Node Count")

                axes[0][1].set_title("Packets in Transmit")
                axes[0][1].set_xlabel(f"Simulation Ticks ({args.ms_per_tick}ms/tick)")
                axes[0][1].set_ylabel(f"Packet Count")

                axes[1][0].set_title("Control Packet Ratio")
                axes[1][0].set_xlabel(f"CPR ({args.ms_per_tick}ms/tick)")
                axes[1][0].set_ylabel(f"CPR (control packets/total packets)")

                axes[1][1].set_title("Instant Control Packet Ratio")
                axes[1][1].set_xlabel(f"Simulation Ticks ({args.ms_per_tick}ms/tick)")
                axes[1][1].set_ylabel(f"CPR (control packets/total packets)")

                sns.lineplot(data=stats["df"]["active_nodes"], ax=axes[0][0], color="orange", legend='brief', label="Active nodes")
                sns.lineplot(data=stats["df"]["dead_nodes"], ax=axes[0][0], color="blue", legend='brief', label="Dead nodes")
                sns.lineplot(data=stats["df"]["packets_in_transmit"], ax=axes[0][1], color="purple", legend='brief', label="Basic packets")
                sns.lineplot(data=stats["df"]["control_packets_sent"], ax=axes[0][1], color="green", legend='brief', label="Control packets")
                sns.lineplot(data=stats["df"]["control_total_cumulative_ratio"], ax=axes[1][0], color="mediumslateblue")
                sns.lineplot(data=stats["df"]["control_basic_instant_ratio"], ax=axes[1][1], color="red")

                nx.draw(T, ax=axes[0][2], with_labels=True, node_color=node_color)
                
                if args.network_type == "grid":   
                    pos = {i: (i // args.node_count_on_edge, i % args.node_count_on_edge) for i in range(total_nodes)}
                    nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color, pos=pos)
                else:
                    nx.draw(N.G, ax=axes[1][2], with_labels=True, node_color=node_color)

                plt.pause(0.0005)

                if args.save_tick_plots:
                    plt.savefig(tick_plots_save_path + f"{str(t).zfill(3)}.png", dpi=160)

            if break_this_tick:
                break

            time.sleep(args.ms_per_tick / 1000)
    except KeyboardInterrupt:
        pass

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

    plt.savefig(f"simdump/DS_stats_{args.network_type}_{total_nodes}_{ts}.png", dpi=200)

    with open(f"simdump/DS_run_{args.network_type}_{total_nodes}_{ts}.pkl", "wb") as fp:
        pickle.dump({
            "args": args,
            "context": topo_context,
            "stats": stats,
            "graphs": graphs
        }, fp)

    if not args.no_realtime_plot:
        plt.show()

    print(f"\n{reason} [{t - stats['terminated_on_tick'] if stats['terminated_on_tick'] is not None else None}]")

    if args.generate_gif:
        make_gif(f"{tick_plots_save_path}/*.png", tick_plots_save_path, "animation.gif", t * 20)