import time
import random
from Channels.Channels import P2PFIFOPerfectChannel
import networkx as nx
from Routing.DBR2P.DBR2PNode import DBR2PNode
from Ahc import Topology
import matplotlib.pyplot as plt
from statistics import mean

edges = [(0, 7, {"weight": 1}),
         (1, 3, {"weight": 1}), (1, 6, {"weight": 1}), (1, 7, {"weight": 1}), (1, 8, {"weight": 1}),
         (2, 4, {"weight": 1}), (2, 5, {"weight": 1}),
         (3, 4, {"weight": 1}), (3, 5, {"weight": 1}), (3, 7, {"weight": 1}),
         (4, 8, {"weight": 1}), (4, 9, {"weight": 1}),
         (5, 8, {"weight": 1}), (5, 9, {"weight": 1}),
         (7, 8, {"weight": 1}),
         ]

# undirected graph
graph = nx.Graph()
graph.add_edges_from(edges)
topology = Topology()
topology.construct_from_graph(graph, DBR2PNode, P2PFIFOPerfectChannel)
topology.start()

pos = nx.spring_layout(graph)
labels = nx.get_edge_attributes(graph, 'weight')
nx.draw(graph, pos, with_labels=True)
nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
plt.show(block=False)
senderID_1 = 0
senderID_2 = 6
receiverID_1 = 2
receiverID_2 = 9
i = 0
sender_1 = topology.nodes[senderID_1]
sender_2 = topology.nodes[senderID_2]
sleeper_list = [4, 5]
while i < 50:
    sleeper_ID = random.choice(sleeper_list)
    sleeper = topology.nodes[sleeper_ID]

    i += 1
    j = 0
    while j < 30:
        j += 1

        sender_1.send_data_to(receiverID_1)
        sender_1.send_data_to(receiverID_2)
        sender_2.send_data_to(receiverID_1)
        sender_2.send_data_to(receiverID_2)

        if j == 10:
            try:
                # sleeper_ID = sender_1.ApplicationComponent.routes[receiverID_1][2]
                # sleeper = topology.nodes[sleeper_ID]
                sleeper.inactive_for_time(3)
                #print(sleeper_ID)
                #sleeper.inactive_for_time(20)
            except Exception as e:
                print(e)
        time.sleep(0.2)

c = input("finish : ")
sender_1 = topology.nodes[senderID_1]
sender_2 = topology.nodes[senderID_2]
print(f"Route discovery time mean:{mean(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_1])}")
print(f"Route discovery time len:{len(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_1])}")

print(f"Route discovery time mean:{mean(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_2])}")
print(f"Route discovery time len:{len(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_1])}")

print(f"Route discovery time mean:{mean(sender_2.ApplicationComponent.message_route_discovery_times[receiverID_1])}")
print(f"Route discovery time len:{len(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_1])}")

print(f"Route discovery time mean:{mean(sender_2.ApplicationComponent.message_route_discovery_times[receiverID_2])}")
print(f"Route discovery time len:{len(sender_1.ApplicationComponent.message_route_discovery_times[receiverID_1])}")
receiver_1 = topology.nodes[receiverID_1]
receiver_2 = topology.nodes[receiverID_2]
print(f"Message receive mean time:{mean(receiver_1.ApplicationComponent.message_arrival_times[senderID_1])}")
print(f"Message receive mean len:{len(receiver_1.ApplicationComponent.message_arrival_times[senderID_1])}")

print(f"Message receive mean time:{mean(receiver_1.ApplicationComponent.message_arrival_times[senderID_2])}")
print(f"Message receive mean len:{len(receiver_1.ApplicationComponent.message_arrival_times[senderID_2])}")

print(f"Message receive mean time:{mean(receiver_2.ApplicationComponent.message_arrival_times[senderID_1])}")
print(f"Message receive mean len:{len(receiver_2.ApplicationComponent.message_arrival_times[senderID_1])}")

print(f"Message receive mean time:{mean(receiver_2.ApplicationComponent.message_arrival_times[senderID_2])}")
print(f"Message receive mean len:{len(receiver_2.ApplicationComponent.message_arrival_times[senderID_2])}")

try:
    print(f"Route discovery backup time mean:{mean(sender_1.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_1])}")
    print(f"Route discovery backup time len:{len(sender_1.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_1])}")
except:
    pass
try:
    print(f"Route discovery backup time mean:{mean(sender_1.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_2])}")
    print(f"Route discovery backup time len:{len(sender_1.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_2])}")
except:
    pass
try:
    print(f"Route discovery backup time mean:{mean(sender_2.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_1])}")
    print(f"Route discovery backup time len:{len(sender_2.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_1])}")
except:
    pass
try:
    print(f"Route discovery backup time mean:{mean(sender_2.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_2])}")
    print(f"Route discovery backup time len:{len(sender_2.ApplicationComponent.message_route_discovery_from_backup_times[receiverID_2])}")
except:
    pass