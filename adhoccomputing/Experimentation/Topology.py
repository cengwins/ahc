from random import sample
import itertools
import networkx as nx
from ..Generics import *
from ..GenericModel import GenericModel

inf = float('inf')
class Topology:
  nodes = {}
  channels = {}

  def __init__(self, name=None) -> None:
#      print("Constructing topology", name)
    pass

  def construct_winslab_topology_with_channels(self, nodecount, nodetype, channeltype, context=None):

    self.construct_winslab_topology_without_channels(nodecount, nodetype, context)

    pairs = list(itertools.permutations(range(nodecount), 2))
    print("Pairs", pairs)
    self.G.add_edges_from(pairs)
    edges = list(self.G.edges)
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)


  def construct_winslab_topology_without_channels(self, nodecount, nodetype, context=None):

    self.G = nx.Graph()
    self.G.add_nodes_from(range(nodecount))  # TODO : Change depending on the

    nodes = list(self.G.nodes)
    for i in nodes:
      cc = nodetype(nodetype.__name__, i,topology=self)
      self.nodes[i] = cc


  def construct_from_graph(self, G: nx.Graph, nodetype, channeltype, context=None):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)
    self.compute_forwarding_table()
    for i in nodes:
      cc = nodetype(nodetype.__name__, i,topology=self)#, self.ForwardingTable)
      #print("I am topology:", self)
      self.nodes[i] = cc
    for k in edges:
      ch = channeltype(channeltype.__name__ + "-" + str(k[0]) + "-" + str(k[1]), str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  def construct_single_node(self, nodetype, instancenumber):
    self.singlenode = nodetype(nodetype.__name__, instancenumber,topology=self)
    self.G = nx.Graph()
    self.G.add_nodes_from([0])
    self.nodes[0] = self.singlenode

  def construct_sender_receiver(self, sendertype, receivertype, channeltype):
    self.sender = sendertype(sendertype.__name__, 0,topology=self)
    self.receiver = receivertype(receivertype.__name__, 1,topology=self)
    ch = channeltype(channeltype.__name__, "0-1")
    self.G = nx.Graph()
    self.G.add_nodes_from([0, 1])
    self.G.add_edges_from([(0, 1)])
    self.nodes[self.sender.componentinstancenumber] = self.sender
    self.nodes[self.sender.componentinstancenumber] = self.receiver
    self.channels[ch.componentinstancenumber] = ch
    self.sender.connect_me_to_channel(ConnectorTypes.DOWN, ch)
    self.receiver.connect_me_to_channel(ConnectorTypes.DOWN, ch)

  def allpairs_shortest_path(self):
    return dict(nx.all_pairs_shortest_path(self.G))

  def shortest_path_to_all(self, myid):
    path = dict(nx.all_pairs_shortest_path(self.G))
    nodecnt = len(self.G.nodes)
    for i in range(nodecnt):
      print(path[myid][i])

  def start(self):
    N = len(self.G.nodes)
    self.compute_forwarding_table()
    for i in self.G.nodes:
      node = self.nodes[i]
      node.initiate_process()

    # self.nodecolors = ['b'] * N
    # self.lock = Lock()

  def compute_forwarding_table(self):
    # N = len(self.G.nodes)
    # print(f"There are {N} nodes")
    # for i in range(N):
    #   for j in range(N):
    #     try:
    #       mypath = path[i][j]
    #       print(f"{i}to{j} path = {path[i][j]} nexthop = {path[i][j][1]}")
    #       self.ForwardingTable[i][j] = path[i][j][1]

    #       print(f"{i}to{j}path = NONE")
    #       self.ForwardingTable[i][j] = inf  # No paths
    #     except IndexError:
    #       print(f"{i}to{j} nexthop = NONE")
    #       self.ForwardingTable[i][j] = i  # There is a path but length = 1 (self)

    # all-seeing eye routing table contruction
    # def print_forwarding_table(self):
    #   registry.print_components()
    #   print('\n'.join([''.join(['{:4}'.format(item) for item in row])
    #                    for row in list(self.ForwardingTable.values())]))
    self.ForwardingTable = dict(nx.all_pairs_shortest_path(self.G))

  # returns the all-seeing eye routing based next hop id
  def get_next_hop(self, fromId, toId):
    try:
      retval = self.ForwardingTable[fromId][toId]
      return retval[1]
    except KeyError:
      return inf
    except IndexError:
      return fromId
  
  # Returns the list of neighbors of a node
  def get_neighbors(self, nodeId):
    return sorted([neighbor for neighbor in self.G.neighbors(nodeId)])


  def get_predecessors(self, nodeId):
    return sorted([neighbor for neighbor in self.G.predecessors(nodeId)])

  def get_successors(self, nodeId):
    return sorted([neighbor for neighbor in self.G.neighbors(nodeId)])

  # Returns the list of neighbors of a node
  def get_neighbor_count(self, nodeId):
    # return len([neighbor for neighbor in self.G.neighbors(nodeId)])
    return self.G.degree[nodeId]

  def plot(self):
    # self.lock.acquire()
    # nx.draw(self.G, self.nodepos, node_color=self.nodecolors, with_labels=True, font_weight='bold')
    # plt.draw()
    print(self.nodecolors)
    # self.lock.release()

  def get_random_node(self):
    return self.nodes[sample(self.G.nodes(), 1)[0]]

