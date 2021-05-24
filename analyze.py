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

snr_distrib = {
    "DS": {
        "erg": {},
        "star": {},
        "grid": {}
    },
    "SF": {
        "erg": {},
        "star": {},
        "grid": {}
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

                if nodes not in snr_distrib["SF"][topo]:
                    snr_distrib["SF"][topo][nodes] = []

                snr_distrib["SF"][topo][nodes].append(0)
            else:
                reason, _, _, _, diff = lines[-1].split()

                assert diff[0] == "[" and diff[-1] == "]"

                if diff[1:-1] != "None":
                    dif = int(diff[1:-1])
                else:
                    dif = 0

                latency["SF"][topo].append((True, dif, dif/nodes))

                if nodes not in snr_distrib["SF"][topo]:
                    snr_distrib["SF"][topo][nodes] = []

                snr_distrib["SF"][topo][nodes].append(1)
        elif algo == "DS":
            reason = lines[-1].split(" ")[0]

            if reason not in ["root", "forced"]:
                raise RuntimeError(reason)

            if reason == "forced":
                latency["DS"][topo].append((False, ))

                if nodes not in snr_distrib["DS"][topo]:
                    snr_distrib["DS"][topo][nodes] = []

                snr_distrib["DS"][topo][nodes].append(0)
            else:
                reason, _, _, diff = lines[-1].split()

                assert diff[0] == "[" and diff[-1] == "]"

                if diff[1:-1] != "None":
                    dif = int(diff[1:-1])
                else:
                    dif = 0

                latency["DS"][topo].append((True, dif, dif/nodes))

                if nodes not in snr_distrib["DS"][topo]:
                    snr_distrib["DS"][topo][nodes] = []

                snr_distrib["DS"][topo][nodes].append(1)
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

fig, axes = plt.subplots(2, 3)
fig.set_figheight(5)
fig.set_figwidth(25)

axes[0][0].set_title("DS/SF Grid LNR Distribution")
axes[0][1].set_title("DS/SF Star LNR Distribution")
axes[0][2].set_title("DS/SF ERG LNR Distribution")
axes[0][0].set_xlabel("Latency/Node Ratio (ticks/node)")
axes[0][1].set_xlabel("Latency/Node Ratio (ticks/node)")
axes[0][2].set_xlabel("Latency/Node Ratio (ticks/node)")

axes[0][0].set_title("Dijkstra-Scholten SNR Plot")
axes[0][1].set_title("Shavit-Francez SNR Plot")
axes[0][0].set_xlabel("Node Count")
axes[0][1].set_xlabel("Node Count")
axes[0][0].set_ylabel("Successive Simulations")
axes[0][1].set_ylabel("Successive Simulations")

sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["grid"], "Shavit-Francez": lnr_distr["SF"]["grid"]}, kde=True, ax=axes[0], log_scale=True)
sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["star"], "Shavit-Francez": lnr_distr["SF"]["star"]}, kde=True, ax=axes[1], log_scale=True)
sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["erg"], "Shavit-Francez": lnr_distr["SF"]["erg"]}, kde=True, ax=axes[2], log_scale=True)

ds_grid_df = pd.DataFrame({
    "succ": [sum(snr_distrib["DS"]["grid"][node_count]) for node_count in snr_distrib["DS"]["grid"]],
    "nodes": [node_count for node_count in snr_distrib["DS"]["grid"]]
})

ds_star_df = pd.DataFrame({
    "succ": [sum(snr_distrib["DS"]["star"][node_count]) for node_count in snr_distrib["DS"]["star"]],
    "nodes": [node_count for node_count in snr_distrib["DS"]["star"]]
})

ds_erg_df = pd.DataFrame({
    "succ": [sum(snr_distrib["DS"]["erg"][node_count]) for node_count in snr_distrib["DS"]["erg"]],
    "nodes": [node_count for node_count in snr_distrib["DS"]["erg"]]
})

sf_grid_df = pd.DataFrame({
    "succ": [sum(snr_distrib["SF"]["grid"][node_count]) for node_count in snr_distrib["SF"]["grid"]],
    "nodes": [node_count for node_count in snr_distrib["SF"]["grid"]]
})

sf_star_df = pd.DataFrame({
    "succ": [sum(snr_distrib["SF"]["star"][node_count]) for node_count in snr_distrib["SF"]["star"]],
    "nodes": [node_count for node_count in snr_distrib["SF"]["star"]]
})

sf_erg_df = pd.DataFrame({
    "succ": [sum(snr_distrib["SF"]["erg"][node_count]) for node_count in snr_distrib["SF"]["erg"]],
    "nodes": [node_count for node_count in snr_distrib["SF"]["erg"]]
})

sns.lineplot(data=ds_grid_df, x="nodes", y="succ", ax=axes[1][0])
sns.lineplot(data=ds_star_df, x="nodes", y="succ", ax=axes[1][0])
sns.lineplot(data=ds_erg_df, x="nodes", y="succ", ax=axes[1][0])

sns.lineplot(data=ds_grid_df, x="nodes", y="succ", ax=axes[1][0])
sns.lineplot(data=ds_star_df, x="nodes", y="succ", ax=axes[1][0])
sns.lineplot(data=ds_erg_df, x="nodes", y="succ", ax=axes[1][0])

sns.despine()
plt.show()
