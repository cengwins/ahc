import os
import sys
import random

from pprint import pprint

sys.path.insert(0, os.getcwd())

from Ahc import Topology
from Channels.Channels import  P2PFIFOPerfectChannel
import networkx as nx
import matplotlib.pyplot as plt
from Routing.SSBR.SSBRNode import SSBRNode

edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
         (3, 5, {"weight": 1})]

NODE_COUNT = input("Enter # of nodes: ")
NODE_COUNT = int(NODE_COUNT)

def draw_random_graph(n):
    k = True
    while k == True:
        k = False
        g_random = nx.gnp_random_graph(n, 0.75)
        if not nx.is_connected(g_random):
            k = True
    return g_random

# Generating random graph
graph =  draw_random_graph(NODE_COUNT)

# Generating non-random graph
#graph = nx.Graph()
#graph.add_edges_from(edges)


# Changing weights
for (u,v,w) in graph.edges(data=True):

    w['weight'] = round(random.uniform(0.01,0.99), 2)

# Drawing the graph
pos = nx.spring_layout(graph)
labels = nx.get_edge_attributes(graph,'weight')
print(labels)
nx.draw(graph, pos, with_labels=True)
nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)

plt.show()
plt.close()

topology = Topology()
topology.construct_from_graph(graph, SSBRNode, P2PFIFOPerfectChannel)
# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()

topology.start()
while True: pass
