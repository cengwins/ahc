import os
import pickle
import seaborn as sns
import matplotlib.pyplot as plt

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
                "wppn": wppn,
                "cwpr": cpr + wpr
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
fig.set_figheight(10)
fig.set_figwidth(25)

axes[0][0].set_title("DS/SF Grid Topology LNR Distribution")
axes[0][1].set_title("DS/SF Star Topology LNR Distribution")
axes[0][2].set_title("DS/SF ERG Topology LNR Distribution")

axes[0][0].set_xlabel("Latency/Node Ratio (ticks/node)")
axes[0][1].set_xlabel("Latency/Node Ratio (ticks/node)")
axes[0][2].set_xlabel("Latency/Node Ratio (ticks/node)")

sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["grid"], "Shavit-Francez": lnr_distr["SF"]["grid"]}, kde=True, ax=axes[0][0], log_scale=True)
sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["star"], "Shavit-Francez": lnr_distr["SF"]["star"]}, kde=True, ax=axes[0][1], log_scale=True)
sns.histplot(data={"Dijkstra-Scholten": lnr_distr["DS"]["erg"], "Shavit-Francez": lnr_distr["SF"]["erg"]}, kde=True, ax=axes[0][2], log_scale=True)

axes[1][0].set_title("DS/SF Grid SNR Topology Plot")
axes[1][1].set_title("DS/SF Star SNR Topology Plot")
axes[1][2].set_title("DS/SF ERG SNR Topology Plot")

axes[1][0].set_xlabel("Node Count")
axes[1][1].set_xlabel("Node Count")
axes[1][2].set_xlabel("Node Count")

axes[1][0].set_ylabel("Successive Simulations (%)")
axes[1][1].set_ylabel("Successive Simulations (%)")
axes[1][2].set_ylabel("Successive Simulations (%)")

topos = [
    "grid",
    "star",
    "erg"
]

for i in range(3):
    sns.lineplot(y=[100 * sum(snr_distrib["DS"][topos[i]][node_count]) / len(snr_distrib["DS"][topos[i]][node_count]) for node_count in snr_distrib["DS"][topos[i]]], x=[node_count for node_count in snr_distrib["DS"][topos[i]]], ax=axes[1][i], legend='brief', label="Dijkstra-Scholten", alpha=0.7)  
    sns.lineplot(y=[100 * sum(snr_distrib["SF"][topos[i]][node_count]) / len(snr_distrib["SF"][topos[i]][node_count]) for node_count in snr_distrib["SF"][topos[i]]], x=[node_count for node_count in snr_distrib["SF"][topos[i]]], ax=axes[1][i], legend='brief', label="Shavit-Francez", alpha=0.7)  

sns.despine()
plt.savefig("lnr_snr.png", dpi=200)

fig, axes = plt.subplots(2, 3)
fig.set_figheight(10)
fig.set_figwidth(25)

axes[0][0].set_title("DS/SF Grid Control Package Ratio Plot")
axes[0][1].set_title("DS/SF Star Control Package Ratio Plot")
axes[0][2].set_title("DS/SF ERG Control Package Ratio Plot")

axes[0][0].set_xlabel("Node Count")
axes[0][1].set_xlabel("Node Count")
axes[0][2].set_xlabel("Node Count")

axes[0][0].set_ylabel("Average CPR (%)")
axes[0][1].set_ylabel("Average CPR (%)")
axes[0][2].set_ylabel("Average CPR (%)")

# axes[0][0].set_yscale("log")
# axes[0][1].set_yscale("log")
# axes[0][2].set_yscale("log")

for i in range(3):
    _top = topos[i]
    cprs = {}
    c_wprs = {}
    c_prs = {}
    wprs = {}

    for x in metrics["DS"][_top]:
        node_count = x[0]
        cpr = x[1]["cpr"]

        if node_count not in cprs:
            cprs[node_count] = []

        cprs[node_count].append(cpr)

    for x in metrics["SF"][_top]:
        node_count = x[0]

        cw_pr = x[1]["cwpr"]
        c_pr = x[1]["cpr"]
        wpr = x[1]["wpr"]

        if node_count not in c_wprs:
            c_wprs[node_count] = []

        if node_count not in c_prs:
            c_prs[node_count] = []

        if node_count not in wprs:
            wprs[node_count] = []

        c_wprs[node_count].append(cw_pr)
        c_prs[node_count].append(c_pr)
        wprs[node_count].append(wpr)

    sns.lineplot(y=[sum(cprs[node_count]) / len(cprs[node_count]) for node_count in cprs], x=[node_count for node_count in cprs], ax=axes[0][i], legend='brief', label="Dijkstra-Scholten (CPR)")  
    sns.lineplot(y=[sum(c_prs[node_count]) / len(c_prs[node_count]) for node_count in c_prs], x=[node_count for node_count in c_prs], ax=axes[0][i], legend='brief', label="Shavit-Francez (CPR)")  
    sns.lineplot(y=[sum(wprs[node_count]) / len(wprs[node_count]) for node_count in wprs], x=[node_count for node_count in wprs], ax=axes[0][i], legend='brief', label="Shavit-Francez (WPR)")  
    sns.lineplot(y=[sum(c_wprs[node_count]) / len(c_wprs[node_count]) for node_count in c_wprs], x=[node_count for node_count in c_wprs], ax=axes[0][i], legend='brief', label="Shavit-Francez (CWPR)")  

axes[1][0].set_title("Dijkstra-Scholten Average CPPN Ratio Plot")
axes[1][1].set_title("Shavit-Francez Average CPPN Ratio Plot")
axes[1][2].set_title("Shavit-Francez Average WPPN Ratio Plot")

axes[1][0].set_xlabel("Node Count")
axes[1][1].set_xlabel("Node Count")
axes[1][2].set_xlabel("Node Count")

axes[1][0].set_ylabel("Average CPPN (control packets/node)")
axes[1][1].set_ylabel("Average CPPN (control packets/node)")
axes[1][2].set_ylabel("Average WPPN (wave packets/node)")

def get_average_cppn(algo, topo):
    cppns = {}

    for x in metrics[algo][topo]:
        node_count = x[0]
        cppn = x[1]["cppn"]

        if node_count not in cppns:
            cppns[node_count] = []

        cppns[node_count].append(cppn)

    return ([sum(cppns[node_count]) / len(cppns[node_count]) for node_count in cppns], [node_count for node_count in cppns])

def get_average_wppn(topo):
    wppns = {}

    for x in metrics["SF"][topo]:
        node_count = x[0]
        wppn = x[1]["wppn"]

        if node_count not in wppns:
            wppns[node_count] = []

        wppns[node_count].append(wppn)

    return ([sum(wppns[node_count]) / len(wppns[node_count]) for node_count in wppns], [node_count for node_count in wppns])

ds_grid_cppns = get_average_cppn("DS", "grid")
ds_star_cppns = get_average_cppn("DS", "star")
ds_erg_cppns = get_average_cppn("DS", "erg")

sf_grid_cppns = get_average_cppn("SF", "grid")
sf_star_cppns = get_average_cppn("SF", "star")
sf_erg_cppns = get_average_cppn("SF", "erg")

sf_grid_wppns = get_average_wppn("grid")
sf_star_wppns = get_average_wppn("star")
sf_erg_wppns = get_average_wppn("erg")

sns.lineplot(y=ds_grid_cppns[0], x=ds_grid_cppns[1], ax=axes[1][0], legend='brief', label="Grid")  
sns.lineplot(y=ds_star_cppns[0], x=ds_star_cppns[1], ax=axes[1][0], legend='brief', label="Star")  
sns.lineplot(y=ds_erg_cppns[0], x=ds_erg_cppns[1], ax=axes[1][0], legend='brief', label="ERG")  

sns.lineplot(y=sf_grid_cppns[0], x=sf_grid_cppns[1], ax=axes[1][1], legend='brief', label="Grid")  
sns.lineplot(y=sf_star_cppns[0], x=sf_star_cppns[1], ax=axes[1][1], legend='brief', label="Star")  
sns.lineplot(y=sf_erg_cppns[0], x=sf_erg_cppns[1], ax=axes[1][1], legend='brief', label="ERG")  

sns.lineplot(y=sf_grid_wppns[0], x=sf_grid_wppns[1], ax=axes[1][2], legend='brief', label="Grid")  
sns.lineplot(y=sf_star_wppns[0], x=sf_star_wppns[1], ax=axes[1][2], legend='brief', label="Star")  
sns.lineplot(y=sf_erg_wppns[0], x=sf_erg_wppns[1], ax=axes[1][2], legend='brief', label="ERG")  

sns.despine()

plt.savefig("cpr_cppn_wpr_wppn.png", dpi=200)
# plt.show()