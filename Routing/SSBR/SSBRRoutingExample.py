import os
import sys
import random

import matplotlib.pyplot as plt
import time as t

sys.path.insert(0, os.getcwd())

from Ahc import ComponentRegistry, Topology
from Channels.Channels import  P2PFIFOPerfectChannel
import networkx as nx
import matplotlib.pyplot as plt
from Routing.SSBR.SSBRNode import SSBRNode
from Routing.SSBR.HelperFunctions import buildRoutingTable, findStrongConnectedLinksForSingleNode, findAllSimplePaths, printSSTForANode, constructStrongRoute, resetRoutingState, benchmarkTest

edges = [(0, 1, {"weight": 1}), (0, 2, {"weight": 1}), (1, 3, {"weight": 1}), (2, 4, {"weight": 1}), (4, 5, {"weight": 1}),
         (3, 5, {"weight": 1})]

NODE_COUNT = input("Enter # of nodes: ")
NODE_COUNT = int(NODE_COUNT)

def draw_random_graph(n):
    k = True
    while k == True:
        k = False
        g_random = nx.gnp_random_graph(n, 0.05)
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

topology = Topology()
topology.construct_from_graph(graph, SSBRNode, P2PFIFOPerfectChannel)


# process1 = MachineLearningNode("MachineLearningNode", 0)
# ComponentRegistry().init()

topology.start()
threshold = input("Enter threshold value for signal strength (between 0 an 1):\n")
threshold = float(threshold)
# Menu

print("\n 0. Find all simple paths between 2 node \n 1. Show graph. \n 2. Print SST for a node. \n 3. Construct strongly connected route for a node. \n 4. Send unicast data between nodes. \n 5. Benchmark test")

menuItem = input("Enter a value to proceed:\n")
menuItem = int(menuItem)
SSBRForwardingTable = []

while(menuItem):
    if menuItem == 0:
        findAllSimplePaths(graph)

    elif menuItem == 1:
        pos = nx.spring_layout(graph)
        labels = nx.get_edge_attributes(graph,'weight')
        #print(labels)
        nx.draw(graph, pos, with_labels=True)
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)

        plt.show(block=False)

    elif menuItem == 2:
        printSSTForANode(NODE_COUNT)

    elif menuItem == 3:
        source = int(input("Enter source node id:\n"))
        target = int(input("Enter target node id:\n"))
        resetRoutingState(NODE_COUNT)
        labels = nx.get_edge_attributes(graph,'weight')
        findStrongConnectedLinksForSingleNode(labels, threshold, NODE_COUNT)
        buildRoutingTable(source, target)
        print(constructStrongRoute(graph, source, target))
        
    elif menuItem == 4:
        source = int(input("Enter source node id:\n"))
        target = int(input("Enter target node id:\n"))
        labels = nx.get_edge_attributes(graph,'weight')
        resetRoutingState(NODE_COUNT)
        findStrongConnectedLinksForSingleNode(labels, threshold, NODE_COUNT)
        buildRoutingTable(source, target)
        SSBRForwardingTable = constructStrongRoute(graph, source,target)

        if len(SSBRForwardingTable) >= 1:
            sourceNode = ComponentRegistry().get_component_by_key("ApplicationAndNetwork", source)
            sourceNode.send_SSBR_unicast_message(target)
            SSBRForwardingTable=[]
        else:
            print(f"No possible route between #{source}-#{target}")

    elif menuItem == 5:
        nodeNumber = []
        time = []
        for x in range (3,42):
            NODE_COUNT = x
            graph =  draw_random_graph(NODE_COUNT)
            for (u,v,w) in graph.edges(data=True):
                 w['weight'] = round(random.uniform(0.01,0.99), 2)
            topology = Topology()
            topology.construct_from_graph(graph, SSBRNode, P2PFIFOPerfectChannel)
            topology.start()
            source = 0
            target = x-1
            labels = nx.get_edge_attributes(graph,'weight')
            start_time = t.time()
            resetRoutingState(NODE_COUNT)
            findStrongConnectedLinksForSingleNode(labels, threshold, NODE_COUNT)
            benchmarkTest(NODE_COUNT)
            nodeNumber.append(x)
            time.append(t.time()-start_time)
            for y in range (0,x):
                sourceNode = ComponentRegistry().get_component_by_key("SSBRNode", source)
                sourceNode.terminate()
                sourceNode = ComponentRegistry().get_component_by_key("ApplicationAndNetwork", source)
                sourceNode.terminate()
                sourceNode = ComponentRegistry().get_component_by_key("FP", source)
                sourceNode.terminate()
                sourceNode = ComponentRegistry().get_component_by_key("DRP", source)
                sourceNode.terminate()
                sourceNode = ComponentRegistry().get_component_by_key("NetworkInterface", source)
                sourceNode.terminate()

        plt.plot(nodeNumber, time)
        plt.title('Node number vs Time')
        plt.xlabel('Node Number')
        plt.ylabel('Time')
        plt.show()

    menuItem = input("Enter a new value to proceed:\n")
    print("0. Find all simple paths between 2 node \n 1. Show graph. \n 2. Print SST for a node. \n 3. Construct strongly connected route for a node. \n 4. Send unicast data between nodes. \n 5. Benchmark test")
    menuItem = int(menuItem)


while True: pass
