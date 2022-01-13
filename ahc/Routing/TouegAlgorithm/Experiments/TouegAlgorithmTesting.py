from ahc.Ahc import Topology
from Channels.Channels import  P2PFIFOPerfectChannel
from Routing.TouegAlgorithm.Experiments.ExperimentDataCollector import ExperimentCollector
import networkx as nx
from Routing.TouegAlgorithm.Experiments.MachineLearningNodeComponent import  MachineLearningNode
from Routing.TouegAlgorithm.Experiments.TouegAlgorithmComponent import TouegRoutingComponent

# edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
#          (3, 5, {"weight": 1})]


# undirected graph
def draw_random_graph(n):
    """
    Draw a random graph with 2**i nodes,
    and p=i/(2**i)
    """
    k = True
    while k == True:
        k = False
        g_random = nx.gnp_random_graph(n, 0.3)
        if not nx.is_connected(g_random):
            k = True

    # nx.draw(g_random, node_size=20)
    # # for e in g_random.edges:
    # #     print(f"{e}")
    # plt.show()
    # plt.close()
    return g_random

# undirected graph
NODE_COUNT = 50
graph =  draw_random_graph(NODE_COUNT) # nx.Graph()
# graph.add_edges_from(edges)

node_list = graph.nodes;

print(TouegRoutingComponent.__name__)
experimenter = ExperimentCollector()

topology = Topology()
topology.construct_from_graph(graph, MachineLearningNode, P2PFIFOPerfectChannel)
# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()
experimenter.network_graph = graph
# topology.plot()
# plt.show()
topology.start()


while True:
    all_completed = True
    for i in node_list:
        if i not in experimenter.COMPLETION:
            all_completed = False

    if not "INIT" in experimenter.COMPLETION:
        all_completed = False

    if all_completed:
        print(experimenter.network_graph)
        print(experimenter.MESSAGE_COUNT)
        print(experimenter.COMPLETION)
        break
    pass

experimenter.storeResult()

