import time
import random
from Channels.Channels import P2PFIFOPerfectChannel
import networkx as nx
from Routing.DBR2P.DBR2PNode import DBR2PNode
from Ahc import Topology
import matplotlib.pyplot as plt
from statistics import mean

edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (0, 3, {"weight": 1}),
         (1, 3, {"weight": 1}), (1, 9, {"weight": 1}),
         (2, 4, {"weight": 1}), (2, 8, {"weight": 1}),
         (3, 4, {"weight": 1}),
         (5, 3, {"weight": 1}), (5, 7, {"weight": 1}),
         (6, 4, {"weight": 1}), (6, 8, {"weight": 1}),
         (7, 4, {"weight": 1}),
         (8, 9, {"weight": 1}),
         ]

# undirected graph
graph = nx.Graph()
graph.add_edges_from(edges)
topology = Topology()
topology.construct_from_graph(graph, DBR2PNode, P2PFIFOPerfectChannel)
# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()
# topology.plot()
# plt.show()
topology.start()
nodeID = 7
receiverID = 9
# pos = nx.spring_layout(graph)
# labels = nx.get_edge_attributes(graph, 'weight')
# # print(labels)
# nx.draw(graph, pos, with_labels=True)
# nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
# plt.show(block=False)
i = 0
while i < 50:
    sender = topology.nodes[nodeID]
    sleeper = topology.nodes[2]
    i += 1
    j = 0
    while j < 30:
        j += 1
        sender.send_data_to(receiverID)
        if j == 5 or j == 15:
            try:
                # print(sender.ApplicationComponent.routes[receiverID][1])
                topology.nodes[sender.ApplicationComponent.routes[receiverID][1]].inactive_for_time(2)
            except:
                pass
        time.sleep(0.2)

c = input("finish : ")
sender = topology.nodes[nodeID]
print(f"Route discovery time mean:{mean(sender.ApplicationComponent.message_route_discovery_times[receiverID])}")
print(f"Route discovery time length:{len(sender.ApplicationComponent.message_route_discovery_times[receiverID])}")
print(f"Route discovery backup time mean:{mean(sender.ApplicationComponent.message_route_discovery_from_backup_times[receiverID])}")
print(f"Route discovery backup time length:{len(sender.ApplicationComponent.message_route_discovery_from_backup_times[receiverID])}")

receiver = topology.nodes[receiverID]
print(f"Message receive mean time:{mean(receiver.ApplicationComponent.message_arrival_times[nodeID])}")
print(f"Message receive length time:{len(receiver.ApplicationComponent.message_arrival_times[nodeID])}")