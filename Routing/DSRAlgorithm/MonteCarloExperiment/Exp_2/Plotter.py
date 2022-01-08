# libraries
import numpy as np
import matplotlib.pyplot as plt

import json
import os


def get_results():
    results = {
        10: {},
        20: {},
        30: {},
        40: {}
    }

    path = "Results"
    directory = os.fsencode(path)

    for file in os.listdir(directory):

        filename = os.fsdecode(file)
        if filename[0] != "R":
            continue
        json_file = open(path + "\\" + filename)
        result_json = json.load(json_file)

        total_node_number = result_json["total_node_number"]
        probability_of_edge = result_json["probability_of_edge"]
        req_time = result_json["time"]["request"]
        reply_time = result_json["time"]["reply"]
        forward_time = result_json["time"]["forwarding"]
        request_message_count = result_json["request_message_count"]
        route_length = result_json["route"][1]["route_node_count"] - 1
        edge_count = len(result_json["edges"])

        try:
            results[total_node_number][route_length].append([req_time,
                                                             reply_time,
                                                             forward_time,
                                                             edge_count])
        except KeyError:
            results[total_node_number][route_length] = []
            results[total_node_number][route_length].append([req_time,
                                                             reply_time,
                                                             forward_time,
                                                             edge_count])

    return results


def plot_graph(results, choice, y_label, y_axis_lim, title, save_path):
    node_number = 10

    prob_list = []

    for route_length in results[node_number]:

        sim_list = []

        for (req_time, reply_time, forward_time, edge_count) in results[node_number][route_length]:
            if 0 == choice:
                sim_list.append(req_time + reply_time)
            elif 1 == choice:
                sim_list.append(forward_time)
            elif 2 == choice:
                sim_list.append(edge_count)

        prob_list.append(sim_list)

    prob_time_array = np.array(prob_list)

    mean_list = []
    for prob_time in prob_time_array:
        mean_list.append(np.mean(prob_time))

    deviation_list = []
    for prob_time in prob_time_array:
        deviation_list.append(np.std(prob_time))

    # Create lists for the plot
    x_axis_labels = []
    for route_length in results[node_number]:
        x_axis_labels.append(route_length)

    x_axis_labels = [str(int(a)) for a in x_axis_labels]

    x_pos = np.arange(len(x_axis_labels))
    CTEs = mean_list
    error = deviation_list

    # Build the plot
    plot_count = node_number / 10
    plt.subplot(1, 1, 1)
    plt.bar(x_pos, CTEs, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
    plt.ylabel(y_label)
    plt.xticks(x_pos, x_axis_labels)

    plt.ylim(y_axis_lim)

    plt.title("Node Count = " + str(node_number) + " and Edge Count = " + str(10))
    plt.gca().yaxis.grid()
    plt.tight_layout()

    plt.subplots_adjust(top=0.85)
    plt.suptitle(title)
    plt.savefig(save_path)

    plt.cla()  # which clears data but not axes
    plt.clf()  # which clears data and axes


result = get_results()
plot_graph(results=result,
           choice=0,
           y_label="Discovery Time in us",
           y_axis_lim=[0, 20000],
           title="Discovery Time vs Route Length",
           save_path="Graphs\\Discovery_Time_Bar_Graphs.png")

plot_graph(results=result,
           choice=1,
           y_label="Forward Time in us",
           y_axis_lim=[0, 5000],
           title="Forward Time vs Route Length",
           save_path="Graphs\\Forward_Time_Bar_Graphs.png")

plot_graph(results=result,
           choice=2,
           y_label="Total Edge Count",
           y_axis_lim=[8, 14],
           title="Total Edge Count vs Route Length",
           save_path="Graphs\\Total_Edge_Count_Bar_Graphs.png")
