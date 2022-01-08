import sys
import time
import json
from threading import Thread

import networkx
import matplotlib.pyplot as plt
from PIL import Image


sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
sys.path.append('../../../..')

from Ahc import Topology, ComponentRegistry
from Channels.Channels import P2PFIFOPerfectChannel
from Routing.DSRAlgorithm.MonteCarloExperiment.AdhocNodeComponent import AdhocNodeComponent
from Routing.DSRAlgorithm.MonteCarloExperiment.DataCollector import DataCollector


def create_connected_graph(node_number: int, prob: float):
    while True:
        nx_graph = networkx.erdos_renyi_graph(node_number, prob)
        if networkx.is_connected(nx_graph):
            break

    return nx_graph


def draw_graph(nx_graph, path, open_img=False):
    src_node_id = 0
    dst_node_id = len(nx_graph.nodes()) - 1

    src_node_color = 1.0
    dst_node_color = 0.5714285714285714

    val_map = {src_node_id: src_node_color,
               dst_node_id: dst_node_color}

    values = [val_map.get(node, 0.25) for node in nx_graph.nodes()]

    networkx.draw(nx_graph, cmap=plt.get_cmap('viridis'), node_color=values, with_labels=True, font_color='white')

    plt.savefig(path)

    print(f"Length of the shortest path between nodes {src_node_id} and {dst_node_id}:")
    print(networkx.shortest_path_length(graph, src_node_id, dst_node_id))
    found_path = networkx.shortest_path(graph, src_node_id, dst_node_id)
    print("Associated path:")
    print(found_path)

    if open_img:
        img = Image.open("C:\\Users\\bsezgin\\Desktop\\topology.png")
        img.show()

    return found_path


def log_result(total_node_number, prob_coefficient, simulation_number, nx_found_path, edges):
    dsr_alg_route = DataCollector().get_found_route()
    prob_of_edge = prob_coefficient / total_node_number
    result = {
        "total_node_number": total_node_number,
        "probability_of_edge": prob_of_edge,
        "time": {
            "request": DataCollector().get_request_time_in_us(),
            "reply": DataCollector().get_reply_time_in_us(),
            "forwarding": DataCollector().get_forwarding_time_in_us()
        },
        "request_message_count": DataCollector().get_request_message_count(),
        "route": [
            {"name": "Shortest Path", "route_node_count": len(nx_found_path), "route": nx_found_path},
            {"name": "DSRAlgorithm Path", "route_node_count": len(dsr_alg_route), "route": dsr_alg_route}
        ],
        "edges": edges
    }

    json_result = json.dumps(result, indent=4)
    json_file = open("Results\\Result_" +
                     str(total_node_number) + "_" +
                     str(prob_coefficient) + "_" +
                     str(simulation_number) + ".json", "w")
    json_file.write(json_result)
    json_file.close()


# MonteCarloAddition
node_number = int(sys.argv[1])
prob_coef = int(sys.argv[2])
sim_number = int(sys.argv[3])

prob = prob_coef / node_number

graph = create_connected_graph(node_number, prob)

networkx_found_path = draw_graph(graph, path="TopologyImages\\Topology_" +
                                             str(node_number) + "_" +
                                             str(prob_coef) + "_" +
                                             str(sim_number) + ".png",
                                 open_img=False)

topology = Topology()
topology.construct_from_graph(graph, AdhocNodeComponent, P2PFIFOPerfectChannel)

topology.start()

time.sleep(1)
print("Sim Started!")
app_comp_0 = ComponentRegistry().get_component_by_key("ApplicationComponent", 0)
last_components_id = node_number - 1
t = Thread(target=app_comp_0.send_data, args=[last_components_id])
t.daemon = True
t.start()

while True:
    if DataCollector().is_sim_ended() and (not DataCollector().is_req_msg_sent_recently()):
        break

    DataCollector().set_req_msg_sent_recently(False)

    sleep_in_ms = 10  # min for windows
    sleep_in_sec = sleep_in_ms / 1000

    time.sleep(sleep_in_sec)

edge_list = []
for edge in graph.edges:
    edge_list.append([edge[0], edge[1]])

log_result(node_number, prob_coef, sim_number, networkx_found_path, edge_list)

sys.exit()
