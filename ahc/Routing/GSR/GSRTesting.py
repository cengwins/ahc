from ahc.Ahc import Topology
from ahc.Channels.Channels import P2PFIFOPerfectChannel
import networkx as nx
from ahc.Routing.GSR.GSRTestingNodeComponent import GSRTestingNode
from ahc.Routing.GSR.RoutingGSRComponent import RoutingGSRComponent


# undirected graph
def draw_random_graph(n):
    k = True
    g_random = None
    while k:
        k = False
        g_random = nx.gnp_random_graph(n, 0.3)
        if not nx.is_connected(g_random):
            k = True
    return g_random


# undirected graph
NODE_COUNT = 10

if __name__ == "__main__":
    graph = draw_random_graph(NODE_COUNT)  # nx.Graph()
    print(graph.edges)
    # graph.add_edges_from(edges)

    node_list = graph.nodes

    print(RoutingGSRComponent.__name__)

    topology = Topology()
    topology.construct_from_graph(graph, GSRTestingNode, P2PFIFOPerfectChannel)
    topology.start()

    while True:
        pass
