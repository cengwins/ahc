import matplotlib.pyplot as plt
import numpy as np
import pickle
import os

results = {}

for node_numbers in (5,10,15,20,25,30):
    result_dir = os.getcwd()+"/Routing/ARA/Results/"+str(node_numbers)
    files = os.listdir(result_dir)
    results[node_numbers] = {"Hops": [], "Time": []}
    print(f"{node_numbers} has {len(files)} results")
    total_file_count = len(files)
    for file in files:
        _ , total_time, total_hops = pickle.load(open(result_dir+"/"+file, "rb"))
        results[node_numbers]["Hops"].append(total_hops)
        results[node_numbers]["Time"].append(total_time)



nodes = ("5", "10", "15","20","25","30")
x_pos = np.arange(len(nodes)*2)

hop_mean = [np.mean(results[node_count]["Hops"]) for node_count in (5,10,15,20,25,30)]
hop_std = [np.std(results[node_count]["Hops"]) for node_count in (5,10,15,20,25,30)]
time_mean = [np.mean(results[node_count]["Time"]) for node_count in (5,10,15,20,25,30)]
time_std = [np.std(results[node_count]["Time"]) for node_count in (5,10,15,20,25,30)]

plots = ["Hops", "Time"]
plot = plots[1]

colors=["blue", "green"]
fig, ax = plt.subplots()
if plot == "Hops":
    ax.bar((1,2,3,4,5,6), hop_mean, yerr=hop_std, align='center', alpha=0.5, ecolor='black', capsize=10, color=colors[0], label="Message")
else:
    ax.bar((1,2,3,4,5,6), time_mean,  align='center', alpha=0.5, ecolor='black', capsize=10, color=colors[1], label="Time")

ax.set_xlabel("Node Count")
ax.set_xticks((1, 2, 3, 4,5,6))
ax.set_xticklabels(nodes)
if plot == "Hops":
    ax.set_ylabel('Total Hop Count')

    ax.set_title("Total Hop Count vs Node Count for ARA Route Discovery")
else:
    ax.set_ylabel('Elapsed Time (sec)')

    ax.set_title("Time vs Node Count for for ARA Route Discovery")

# ax.yaxis.grid(True)

# Save the figure and show
plt.tight_layout()
# plt.savefig('bar_plot_'+plot+'.png')
# plt.legend(loc=2)
plt.show()



