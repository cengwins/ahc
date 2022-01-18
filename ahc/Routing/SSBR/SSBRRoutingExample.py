import os
import sys
import random

import numpy as np
import matplotlib.pyplot as plt
import time as t

sys.path.insert(0, os.getcwd())

from ahc.Ahc import ComponentRegistry, Topology
from ahc.Channels.Channels import  P2PFIFOPerfectChannel
import networkx as nx
import matplotlib.pyplot as plt
from ahc.Routing.SSBR.SSBRNode import SSBRNode
from ahc.Routing.SSBR.HelperFunctions import buildRoutingTable, findStrongConnectedLinksForSingleNode, printSSTInfo, constructStrongRoute, resetRoutingState, benchmarkTest

NODE_COUNT = input("Enter # of nodes: ")
NODE_COUNT = int(NODE_COUNT)

def draw_random_graph(n):
    k = True
    while k == True:
        k = False
        g_random = nx.gnp_random_graph(n, 0.45)
        if not nx.is_connected(g_random):
            k = True
    return g_random

# Generating random graph
graph =  draw_random_graph(NODE_COUNT)

# Changing weights
for (u,v,w) in graph.edges(data=True):

    w['weight'] = round(random.uniform(0.01,0.99), 2)

# Drawing the graph
topology = Topology()
topology.construct_from_graph(graph, SSBRNode, P2PFIFOPerfectChannel)

topology.start()
threshold = input("Enter threshold value for signal strength (between 0 an 1):\n")
threshold = float(threshold)

# Menu
print("\n 1. Show graph. \n 2. Print information. \n 3. Construct strongly connected route for a node. \n 4. Send unicast data between nodes. \n 5. Benchmark test")

menuItem = input("Enter a value to proceed:\n")
menuItem = int(menuItem)
SSBRForwardingTable = []

while(menuItem):

    if menuItem == 1:
        pos = nx.spring_layout(graph)
        labels = nx.get_edge_attributes(graph,'weight')
        #print(labels)
        nx.draw(graph, pos, with_labels=True)
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)

        plt.show(block=False)

    elif menuItem == 2:
        printSSTInfo(NODE_COUNT)

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
        rows, cols = (10, 10)
        nodeNumber = [[0 for i in range(cols)] for j in range(rows)]
        time = [[0 for i in range(cols)] for j in range(rows)]
        controlTime = [[0 for i in range(cols)] for j in range(rows)]
        dataTime = [[0 for i in range(cols)] for j in range(rows)]
        for i in range (0,10):
            for x in range (3,13):
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
                controlTime[i][x-3] = (t.time()-start_time)
                start_time2 = t.time()
                benchmarkTest(NODE_COUNT)
                nodeNumber[i][x-3] = x
                dataTime[i][x-3] = (t.time()-start_time2)
                time[i][x-3] = (t.time()-start_time)
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

        resTime = [0]*10
        resNode = [0]*10
        resControlTime = [0]*10
        resDataTime = [0]*10

        for i in range (0,10):
            for k in range (0,10):
                resTime[i] += time[k][i]
                resNode[i] += nodeNumber[k][i]
                resControlTime[i] += controlTime[k][i]
                resDataTime[i] += dataTime[k][i]

        for i in range (0,10):
            resTime[i] /= 10
            resNode[i] /= 10
            resControlTime[i] /= 10
            resDataTime[i] /= 10

        plt.plot(resNode, resTime, label = "Overall Time")
        plt.plot(resNode, resControlTime, label = "Control Plane Time")
        plt.plot(resNode, resDataTime, label = "Data Plane Time")
        plt.grid(color='b', linestyle='-', linewidth=0.2)
        plt.legend()
        plt.title('Node number vs Time')
        plt.xlabel('Node Number')
        plt.ylabel('Time')
        plt.show()

    menuItem = input("Enter a new value to proceed:\n")
    print("\n 1. Show graph. \n 2. Print information. \n 3. Construct strongly connected route for a node. \n 4. Send unicast data between nodes. \n 5. Benchmark test")
    menuItem = int(menuItem)


while True: pass
