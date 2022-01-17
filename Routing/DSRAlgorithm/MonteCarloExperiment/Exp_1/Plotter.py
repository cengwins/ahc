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
        discovery_time = result_json["time"]["request"] + result_json["time"]["reply"]
        request_message_count = result_json["request_message_count"]
        route_length = result_json["route"][1]["route_node_count"] - 1
        edge_count = len(result_json["edges"])

        try:
            results[total_node_number][probability_of_edge].append([discovery_time,
                                                                    request_message_count,
                                                                    route_length,
                                                                    edge_count])
        except KeyError:
            results[total_node_number][probability_of_edge] = []
            results[total_node_number][probability_of_edge].append([discovery_time,
                                                                    request_message_count,
                                                                    route_length,
                                                                    edge_count])

    return results


def plot_graph(results, choice, y_label, y_axis_lim, title, save_path):
    for node_number in results:

        prob_list = []

        for prob in results[node_number]:

            sim_list = []

            for (req_time, req_msg, route_len, edge_count) in results[node_number][prob]:
                if 0 == choice:
                    sim_list.append(req_time)
                elif 1 == choice:
                    sim_list.append(req_msg)
                elif 2 == choice:
                    sim_list.append(route_len)
                elif 3 == choice:
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
        for prob in results[node_number]:
            x_axis_labels.append(prob)

        x_axis_labels = [str(float("{:.2f}".format(a))) for a in x_axis_labels]

        x_pos = np.arange(len(x_axis_labels))
        CTEs = mean_list
        error = deviation_list

        # Build the plot
        plot_count = node_number / 10
        plt.subplot(2, 2, int(plot_count))
        plt.bar(x_pos, CTEs, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
        plt.ylabel(y_label)
        plt.xticks(x_pos, x_axis_labels)

        plt.ylim(y_axis_lim)

        plt.title('Node Count = ' + str(node_number))
        plt.gca().yaxis.grid()
        plt.tight_layout()

    plt.subplots_adjust(top=0.85)
    plt.suptitle(title)
    plt.savefig(save_path)

    plt.cla()  # which clears data but not axes
    plt.clf()  # which clears data and axes


result = get_results()
# plot_graph(results=result,
#            choice=0,
#            y_label="Discovery Time in us",
#            y_axis_lim=[0, 80000],
#            title="Discovery Time vs Prob. of Edge for Node",
#            save_path="Graphs\\Discovery_Time_Bar_Graphs.png")

plot_graph(results=result,
           choice=1,
           y_label="Request Msg Count",
           y_axis_lim=[0, 500],
           title="Request Msg Count vs Prob. of Edge for Node",
           save_path="Graphs\\Request_Msg_Count_Bar_Graphs.png")

# plot_graph(results=result,
#            choice=2,
#            y_label="Route Length",
#            y_axis_lim=[0, 10],
#            title="Route Length vs Prob. of Edge for Node",
#            save_path="Graphs\\Route_Length_Bar_Graphs.png")

plot_graph(results=result,
           choice=3,
           y_label="Total Edge Count",
           y_axis_lim=[0, 200],
           title="Total Edge Count vs Prob. of Edge for Node",
           save_path="Graphs\\Total_Edge_Count_Bar_Graphs.png")
