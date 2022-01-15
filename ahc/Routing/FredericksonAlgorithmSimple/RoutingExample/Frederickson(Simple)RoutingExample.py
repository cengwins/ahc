from ahc.Ahc import Topology
from Channels.Channels import  P2PFIFOPerfectChannel
import networkx as nx
from Routing.FredericksonAlgorithmSimple.RoutingExample.MachineLearningNodeComponent import MachineLearningNode

edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
         (3, 5, {"weight": 1})]

# undirected graph
graph = nx.Graph()
graph.add_edges_from(edges)

topology = Topology()
topology.construct_from_graph(graph, MachineLearningNode, P2PFIFOPerfectChannel)
# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()

topology.start()
while True: pass

