from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

import networkx as nx
from Routing.FredericksonAlgorithmAdvanced.Experiments.MachineLearningNodeComponent import MachineLearningNode
from Routing.FredericksonAlgorithmAdvanced.Experiments.ExperimentDataCollector import ExperimentCollector
edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
         (3, 5, {"weight": 1})]

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

    nx.draw(g_random, node_size=20)
    # for e in g_random.edges:
    #     print(f"{e}")
    # plt.show()
    # plt.close()
    return g_random

# network_graph, MESSAGE_COUNT, COMPLETION, route_table = pickle.load(open("Temp/51416.619156172.exp", "rb"))
NODE_COUNT = 40
graph =  draw_random_graph(NODE_COUNT) # nx.Graph()
experimenter = ExperimentCollector()
import math
l = len(graph.nodes) / math.sqrt(len(graph.edges))
if int(l) == 0:
    l = 1
else:
    l = int(l)

experimenter.l_parameter = 1
node_list = graph.nodes;
print(f"List : {node_list}")

topology = Topology()
topology.construct_from_graph(graph, MachineLearningNode, P2PFIFOPerfectChannel)
# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()
# topology.plot()
# plt.show()
experimenter.network_graph = graph


topology.start()

while True:
    all_completed = True

    if not "INIT" in experimenter.COMPLETION:
        all_completed = False

    if all_completed:
        print(experimenter.network_graph)
        print(experimenter.MESSAGE_COUNT)
        print(experimenter.COMPLETION)
        break
    pass

experimenter.storeResult()
lst = []
for a in experimenter.route_table:
    for k in a:
        if not k in lst:
            lst.append(k)
print(sorted(lst))
print(len(lst) == NODE_COUNT)

