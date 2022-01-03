from networkx import Graph

from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel
from Routing.DSRAlgorithm.RoutingExample.AdhocNodeComponent import AdhocNodeComponent

edges = [(0, 1, {"weight": 1}),
         (0, 2, {"weight": 1}),
         (1, 3, {"weight": 1}),
         (2, 4, {"weight": 1}),
         (4, 5, {"weight": 1}),
         (3, 5, {"weight": 1})]

graph = Graph()
graph.add_edges_from(edges)

topology = Topology()
topology.construct_from_graph(graph, AdhocNodeComponent, P2PFIFOPerfectChannel)

topology.start()
while True:
    pass
