import math
import random
from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx
import threading
from time import sleep
from itertools import combinations, groupby
from math import cos, sin, atan2, radians

from MutualExclusion.RicartAgrawala import RicartAgrawalaNode
from Ahc import Topology
from Channels import P2PFIFOPerfectChannel

FPS = 24.0

EDGE_COLOR = '#7F7F7F'

PRIVILEGED_NODE_COLOR = '#FF0000'
WAITING_NODE_COLOR = '#FFFF00'
NODE_COLOR = '#00FF00'

drawnGraphNodeColors = []
drawnGraphNodeClockValues = []


class COMMAND(Enum):
    DRAW = "draw"
    REQUEST = "request"
    HELP = "help"
    SET = "set"
    GET = "get"


class ARGUMENT(Enum):
    ALL = "-all"
    TIME = "-time"
    REQUEST = "-request"
    REPLY = "-reply"
    PRIVILEGE = "-privilege"
    FORWARDED = "-forwarded"
    MEAN = "-mean"

def processUserCommand(userInput: str):
    try:
        splitInput = userInput.split()
        cmd = splitInput[0]
        args = []
        if len(splitInput) > 1:
            args = splitInput[1:]

        if cmd == COMMAND.REQUEST.value:
            requestCommand(args)
        elif cmd == COMMAND.DRAW.value:
            drawCommand(args)
        elif cmd == COMMAND.SET.value:
            setCommand(args)
        elif cmd == COMMAND.GET.value:
            getCommand(args)
        elif cmd == COMMAND.HELP.value:
            helpCommand()
        else:
            print(f"Unknown input: \'{userInput}\'")
    except IndexError:
        pass

def helpCommand(cmd=COMMAND.HELP):
    if cmd is COMMAND.REQUEST:
        print(f"Request:\n"
              f"\t\"{COMMAND.REQUEST.value} nodeId\"\n"
              f"\t\"{COMMAND.REQUEST.value} nodeId1 nodeId2...\"\n"
              f"\t\"{COMMAND.REQUEST.value} {ARGUMENT.ALL.value}\"")
    elif cmd is COMMAND.DRAW:
        print(f"Draw:\n"
              f"\t\"{COMMAND.DRAW.value}\"")
    elif cmd is COMMAND.SET:
        print(f"Set:\n"
              f"\t\"{COMMAND.SET.value} {ARGUMENT.TIME.value} t\"")
    elif cmd is COMMAND.GET:
        print(f"Get:\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.TIME.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value} nodeId\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value} [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}]\"\n"
              f"\t\"{COMMAND.GET.value} [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}] nodeId\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.MEAN.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.MEAN.value} [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}]\"")
    else:
        helpCommand(COMMAND.REQUEST)
        helpCommand(COMMAND.DRAW)
        helpCommand(COMMAND.SET)
        helpCommand(COMMAND.GET)

def requestCommand(args):
    allNodes = ARGUMENT.ALL.value in args
    if allNodes:
        args.remove(ARGUMENT.ALL.value)

        if len(args) == 0:
            for nodeID in Topology().nodes:
                Topology().nodes[nodeID].send_request()
        else:
            helpCommand(COMMAND.REQUEST)
    else:
        nodes = list()
        for arg in args:
            try:
                nodeID = int(arg)
                node = Topology().nodes[nodeID]
                nodes.append(node)
            except KeyError:
                print(f"Node {nodeID} does not exist in the topology.")
            except ValueError:
                print(f"\'{arg}\' is not integer.")

        if nodes:
            for node in nodes:
                node.send_request()
        else:
            helpCommand(COMMAND.REQUEST)

def drawCommand(args):
    if len(args) == 0:
        drawGraph(True)
    else:
        helpCommand(COMMAND.DRAW)

def setCommand(args):
    if len(args) == 2:
        setTime = ARGUMENT.TIME.value in args

        if setTime:
            args.remove(ARGUMENT.TIME.value)
            try:
                t = float(args[0])
                if t > 0:
                    RicartAgrawalaNode.privilegeSleepAmount = t
                else:
                    print(f"Sleep time cannot be set to {t}, choose a value above 0!")
            except ValueError:
                print(f"\'{args[0]}\' is not float.")
    else:
        helpCommand(COMMAND.SET)

def getNodeInformation(node: RicartAgrawalaNode, request=True, reply=True, privilege=True, forwarded=True):
    information = []

    if request:
        information.append(f"ReceivedRequests: {node.receivedRequestCount}")
        information.append(f"SentRequests: {node.sentRequestCount}")
    if reply:
        information.append(f"ReceivedReplies: {node.receivedReplyCount}")
        information.append(f"SentReplies: {node.sentReplyCount}")
    if privilege:
        information.append(f"Privileged: {node.privilegeCount}")
    if forwarded:
        information.append(f"ForwardedMessages: {node.forwardedMessageCount}")

    return f"{node.componentinstancenumber} => " + " | ".join(information)

def getCommand(args):
    isTime = ARGUMENT.TIME.value in args

    isAll = ARGUMENT.ALL.value in args
    isMean = ARGUMENT.MEAN.value in args

    isRequest = ARGUMENT.REQUEST.value in args
    isReply = ARGUMENT.REPLY.value in args
    isPrivilege = ARGUMENT.PRIVILEGE.value in args
    isForwarded = ARGUMENT.FORWARDED.value in args
    areAnyOtherArgumentsSet = isRequest or isReply or isPrivilege or isForwarded

    if isTime:
        args.remove(ARGUMENT.TIME.value)
    if isAll:
        args.remove(ARGUMENT.ALL.value)
    if isMean:
        args.remove(ARGUMENT.MEAN.value)
    if isRequest:
        args.remove(ARGUMENT.REQUEST.value)
    if isReply:
        args.remove(ARGUMENT.REPLY.value)
    if isPrivilege:
        args.remove(ARGUMENT.PRIVILEGE.value)
    if isForwarded:
        args.remove(ARGUMENT.FORWARDED.value)

    if isTime and not isAll and not isMean:
        if len(args) == 0 and not areAnyOtherArgumentsSet:
            print(f"Sleep amount in critical section is {RicartAgrawalaNode.privilegeSleepAmount} seconds.")
        else:
            helpCommand(COMMAND.GET)
    elif isAll and not isTime and not isMean:
        if not areAnyOtherArgumentsSet:
            isRequest = isReply = isPrivilege = isForwarded = True

        if len(args) == 0:
            for nodeID in Topology().nodes:
                node = Topology().nodes[nodeID]
                print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
        else:
            helpCommand(COMMAND.GET)
    elif isMean and not isTime and not isAll:
        if not areAnyOtherArgumentsSet:
            isRequest = isReply = isPrivilege = isForwarded = True

        if len(args) == 0:
            N = len(Topology().nodes)
            node = RicartAgrawalaNode("", f"Mean of {N} Nodes")

            for nodeID in Topology().nodes:
                node.privilegeCount += Topology().nodes[nodeID].privilegeCount
                node.sentRequestCount += Topology().nodes[nodeID].sentRequestCount
                node.sentReplyCount += Topology().nodes[nodeID].sentReplyCount
                node.receivedRequestCount += Topology().nodes[nodeID].receivedRequestCount
                node.receivedReplyCount += Topology().nodes[nodeID].receivedReplyCount
                node.forwardedMessageCount += Topology().nodes[nodeID].forwardedMessageCount

            node.privilegeCount /= N
            node.sentRequestCount /= N
            node.sentReplyCount /= N
            node.receivedRequestCount /= N
            node.receivedReplyCount /= N
            node.forwardedMessageCount /= N

            print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
        else:
            helpCommand(COMMAND.GET)
    else:
        if areAnyOtherArgumentsSet and not isTime and not isAll and not isMean:
            if len(args) == 1:
                try:
                    nodeID = int(args[0])
                    node = Topology().nodes[nodeID]
                    print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
                except KeyError:
                    print(f"Node {nodeID} does not exist in the topology.")
                except ValueError:
                    print(f"\'{args[0]}\' is not integer.")
            else:
                helpCommand(COMMAND.GET)
        else:
            helpCommand(COMMAND.GET)

def drawGraph(overwrite=False):
    global drawnGraphNodeColors, drawnGraphNodeClockValues

    G = Topology().G
    pos = nx.circular_layout(G, center=(0, 0))

    nodeColors = []
    clockValues = []
    for nodeID in Topology().nodes:
        node = Topology().nodes[nodeID]
        G.nodes[nodeID]['clock'] = node.clock
        clockValues.append(node.clock)

        if node.isPrivileged:
            nodeColors.append(PRIVILEGED_NODE_COLOR)
        elif node.havePendingRequest:
            nodeColors.append(WAITING_NODE_COLOR)
        else:
            nodeColors.append(NODE_COLOR)

    if overwrite or nodeColors != drawnGraphNodeColors or clockValues != drawnGraphNodeClockValues:
        drawnGraphNodeColors = list(nodeColors)
        drawnGraphNodeClockValues = list(clockValues)

        clockLabelsPos = {}
        for key in pos:
            x, y = pos[key]
            r = math.sqrt(x**2 + y**2)
            theta = atan2(y, x) + radians(75)
            d = 0.1
            clockLabelsPos[key] = (x + d * cos(theta), y + d * sin(theta))

        nodeClockLabels = nx.get_node_attributes(G, 'clock')
        nx.draw(G, pos, node_color=nodeColors, edge_color=EDGE_COLOR, with_labels=True, font_weight='bold')
        nx.draw_networkx_labels(G, clockLabelsPos, nodeClockLabels)

        plt.draw()
        plt.show()

def graphDrawingDaemon():
    while True:
        drawGraph()
        sleep(1.0/FPS)

def completeBinomialGraph(n, p):
    if p <= 0:
        G = nx.empty_graph(n)
    elif p >= 1:
        G = nx.complete_graph(n)
    else:
        allEdges = list(combinations(range(n), 2))
        G = nx.empty_graph(n)

        for node, nodeEdges in groupby(allEdges, key=lambda x: x[0]):
            nodeEdges = list(nodeEdges)
            randomEdge = random.choice(nodeEdges)
            G.add_edge(*randomEdge)
            for edge in nodeEdges:
                if random.random() < p:
                    G.add_edge(*edge)

    return G

def main():
    G = completeBinomialGraph(20, 1.000001)

    topology = Topology()
    topology.construct_from_graph(G, RicartAgrawalaNode, P2PFIFOPerfectChannel)
    topology.start()

    graphDaemon = threading.Thread(target=graphDrawingDaemon, daemon=True)
    graphDaemon.start()

    while True:
        userInput = input("User Command: \n")
        processUserCommand(userInput)


if __name__ == "__main__":
    main()
