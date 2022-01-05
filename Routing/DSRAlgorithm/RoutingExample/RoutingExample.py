import networkx
import matplotlib.pyplot as plt
from PIL import Image

from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel
from Routing.DSRAlgorithm.RoutingExample.AdhocNodeComponent import AdhocNodeComponent


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
    print("Associated path:")
    print(networkx.shortest_path(graph, src_node_id, dst_node_id))

    if open_img:
        img = Image.open("C:\\Users\\bsezgin\\Desktop\\topology.png")
        img.show()


node_number = 40
prob_coef = 2
prob = prob_coef/node_number
graph = create_connected_graph(node_number=node_number, prob=prob)

draw_graph(graph, path="C:\\Users\\bsezgin\\Desktop\\topology.png", open_img=False)

topology = Topology()
topology.construct_from_graph(graph, AdhocNodeComponent, P2PFIFOPerfectChannel)

topology.start()
while True:
    pass
