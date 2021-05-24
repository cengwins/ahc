import os
import sys
import time
import json
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

metrics = {
    "DS": {
        "erg": [],
        "star": [],
        "grid": []
    },
    "SF": {
        "erg": [],
        "star": [],
        "grid": []
    }
}

latency = {
    "DS": {
        "erg": [],
        "star": [],
        "grid": []
    },
    "SF": {
        "erg": [],
        "star": [],
        "grid": []
    }
}

lnr_distr = {
    "DS": {
        "erg": None,
        "star": None,
        "grid": None
    },
    "SF": {
        "erg": None,
        "star": None,
        "grid": None
    }
}


for fpath in os.listdir("bench_dump/simdump/"):
    if fpath.endswith(".pkl"):
        algo, _, topo, nodes, _ = fpath.split("_")
        nodes = int(nodes)

        # print(f"++ {algo} {topo} {nodes}")

        with open(f"bench_dump/simdump/{fpath}", "rb") as fp:
            data = pickle.load(fp)

        cpr = list(data["stats"]["df"]["control_total_cumulative_ratio"])[-1]
        cppn = sum(list(data["stats"]["df"]["control_packets_sent"])) / nodes

        if algo == "SF":
            wpr = list(data["stats"]["df"]["wave_total_cumulative_ratio"])[-1]
            wppn = sum(list(data["stats"]["df"]["wave_packets_sent"])) / nodes

            metrics["SF"][topo].append((nodes, {
                "cpr": cpr,
                "wpr": wpr,
                "cppn": cppn,
                "wppn": wppn
            }))
        elif algo == "DS":
            metrics["DS"][topo].append((nodes, {
                "cpr": cpr,
                "cppn": cppn,
            }))
        else:
            raise RuntimeError(algo)

for fpath in os.listdir("bench_dump/"):
    if fpath.endswith(".out"):
        algo, topo, nodes, _ = fpath.split("_")
        nodes = int(nodes)

        if topo == "grid":
            nodes = nodes ** 2
        elif topo == "star":
            nodes = nodes + 1
        elif topo == "erg":
            pass
        else:
            raise RuntimeError(topo)

        # print(f"## {algo} {topo} {nodes} ({fpath})")

        try:
            with open(f"bench_dump/{fpath}", "r") as fp:
                lines = fp.readlines()
        except UnicodeDecodeError as e:
            print(f"[!!!] UnicodeDecodeError ({fpath}): {e}")
            continue

        if algo == "SF":
            reason = lines[-1].split(" ")[0]

            if reason not in ["wave", "forced"]:
                raise RuntimeError(reason)

            if reason == "forced":
                latency["SF"][topo].append((False, ))
            else:
                reason, _, _, _, diff = lines[-1].split()

                assert diff[0] == "[" and diff[-1] == "]"

                if diff[1:-1] != "None":
                    dif = int(diff[1:-1])
                else:
                    dif = 0

                latency["SF"][topo].append((True, dif, dif/nodes))
        elif algo == "DS":
            reason = lines[-1].split(" ")[0]

            if reason not in ["root", "forced"]:
                raise RuntimeError(reason)

            if reason == "forced":
                latency["DS"][topo].append((False, ))
            else:
                reason, _, _, diff = lines[-1].split()

                assert diff[0] == "[" and diff[-1] == "]"

                if diff[1:-1] != "None":
                    dif = int(diff[1:-1])
                else:
                    dif = 0

                latency["DS"][topo].append((True, dif, dif/nodes))
        else:
            raise RuntimeError(algo)

for algo in lnr_distr:
    for topo in lnr_distr[algo]:
        lnr_distr[algo][topo] = [x[-1] for x in latency[algo][topo] if x[0] and x[-1] > 0]

# print(json.dumps({
#     "metrics": metrics,
#     "latency": latency,
#     "lnr": lnr_distr
# }, indent=4))

plot_all = False

if plot_all:
    fig, axes = plt.subplots(2, 3)
    fig.set_figheight(10)
    fig.set_figwidth(30)
    # fig.tight_layout()

    axes[0][0].set_title("Dijkstra-Scholten Grid LNR Distribution")
    axes[0][1].set_title("Dijkstra-Scholten Star LNR Distribution")
    axes[0][2].set_title("Dijkstra-Scholten ERG LNR Distribution")
    axes[1][0].set_title("Shavit-Francez Grid LNR Distribution")
    axes[1][1].set_title("Shavit-Francez Star LNR Distribution")
    axes[1][2].set_title("Shavit-Francez ERG LNR Distribution")

    sns.histplot(data=lnr_distr["DS"]["grid"], kde=True, ax=axes[0][0])
    sns.histplot(data=lnr_distr["DS"]["star"], kde=True, ax=axes[0][1])
    sns.histplot(data=lnr_distr["DS"]["erg"], kde=True, ax=axes[0][2])
    sns.histplot(data=lnr_distr["SF"]["grid"], kde=True, ax=axes[1][0])
    sns.histplot(data=lnr_distr["SF"]["star"], kde=True, ax=axes[1][1])
    sns.histplot(data=lnr_distr["SF"]["erg"], kde=True, ax=axes[1][2])
else:
    fig, axes = plt.subplots(1, 3)
    fig.set_figheight(5)
    fig.set_figwidth(25)

    axes[0].set_title("DS/SF Grid LNR Distribution")
    axes[1].set_title("DS/SF Star LNR Distribution")
    axes[2].set_title("DS/SF ERG LNR Distribution")
    axes[0].set_xlabel("Latency/Node Ratio (ticks/node)")
    axes[1].set_xlabel("Latency/Node Ratio (ticks/node)")
    axes[2].set_xlabel("Latency/Node Ratio (ticks/node)")

    sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["grid"], "Shavit-Francez": lnr_distr["SF"]["grid"]}, kde=True, ax=axes[0], log_scale=True)
    sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["star"], "Shavit-Francez": lnr_distr["SF"]["star"]}, kde=True, ax=axes[1], log_scale=True)
    sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["erg"], "Shavit-Francez": lnr_distr["SF"]["erg"]}, kde=True, ax=axes[2], log_scale=True)

sns.despine()
plt.show()
