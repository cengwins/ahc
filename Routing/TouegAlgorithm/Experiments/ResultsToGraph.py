import matplotlib.pyplot as plt
import numpy as np
import pickle
import os

results = {}

for node_numbers in (10, 20, 30):
    result_dir = "Results/"+str(node_numbers)+"Nodes"
    files = os.listdir(result_dir)
    results[node_numbers] = {"Message": [], "Time": []}
    print(f"{node_numbers} has {len(files)} results")
    for file in files:
        network_graph, MESSAGE_COUNT, COMPLETION, route_table = pickle.load(open(result_dir+"/"+file, "rb"))
        summation = 0
        for count in MESSAGE_COUNT:
            summation+=MESSAGE_COUNT[count]
        results[node_numbers]["Message"].append(summation)
        print(MESSAGE_COUNT)
        results[node_numbers]["Time"].append(COMPLETION["INIT"])
        print(COMPLETION["INIT"])

        if len(network_graph.nodes) != node_numbers:
            raise Exception("Wrong storage")



nodes = ("10", "20", "30")
x_pos = np.arange(len(nodes)*2)

means_message = [np.mean(results[node_count]["Message"]) for node_count in (10, 20, 30)]
errors_message = [np.std(results[node_count]["Message"]) for node_count in (10, 20, 30)]

means_time = [np.mean(results[node_count]["Time"]) for node_count in (10, 20, 30)]
errors_time = [np.std(results[node_count]["Time"]) for node_count in (10, 20, 30)]

means = []
errors = []
for i in range(len(means_time)):
    means.append(means_message[i])
    means.append(means_time[i])
    errors.append(errors_message[i])
    errors.append(errors_time[i])

plots = ["Message", "Time"]
plot = plots[1]

colors=["blue", "green"]
fig, ax = plt.subplots()
if plot == "Message":
    ax.bar((1,   2,   3), means_message, yerr=errors_message, align='center', alpha=0.5, ecolor='black', capsize=10, color=colors[0], label="Message")
else:
    ax.bar((  1,   2,   3), means_time, yerr=errors_time, align='center', alpha=0.5, ecolor='black', capsize=10, color=colors[1], label="Time")

ax.set_xlabel("Node Count")
ax.set_xticks((1, 2, 3))
ax.set_xticklabels(nodes)
if plot == "Message":
    ax.set_ylabel('Message Count')

    ax.set_title("Message Count vs Node Count for Toueg's Algorithm")
else:
    ax.set_ylabel('Elapsed Time (sec)')

    ax.set_title("Time vs Node Count for Toueg's Algorithm")

# ax.yaxis.grid(True)

# Save the figure and show
plt.tight_layout()
plt.savefig('bar_plot_'+plot+'.png')
# plt.legend(loc=2)
plt.show()



