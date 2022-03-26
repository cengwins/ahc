from helpers import *
from generics import *
from definitions import *
from enum import Enum
from threading import Thread, Lock
from random import sample
import networkx as nx
import itertools
import queue

inf = float('inf')

class ConnectorList(dict):
  def __setitem__(self, key, value):
    try:
      self[key]
    except KeyError:
      super(ConnectorList, self).__setitem__(key, [])
    self[key].append(value)
    
  class FramerObjects():
    framerobjects = {}
    ahcuhdubjects = {}
    def add_framer(self, id, obj):
        self.framerobjects[id] = obj
    
    def get_framer_by_id(self, id):
        return self.framerobjects[id]

    def add_ahcuhd(self, id, obj):
        self.ahcuhdubjects[id] = obj
    
    def get_ahcuhd_by_id(self, id):
        return self.ahcuhdubjects[id]

class ComponentRegistry:
  components = {}

  def get_component_by_instance(self, instance):
    list_of_keys = list()
    list_of_items = self.components.items()
    for item in list_of_items:
      if item[1] == instance:
        list_of_keys.append(item[0])
    return list_of_keys

  def add_component(self, component):
    key = component.componentname + str(component.componentinstancenumber)
    self.components[key] = component

  def get_component_by_key(self, componentname, componentinstancenumber):
    key = componentname + str(componentinstancenumber)
    return self.components[key]

  def init(self):
    for itemkey in self.components:
      cmp = self.components[itemkey]
      cmp.inputqueue.put_nowait(Event(self, EventTypes.INIT, None))
      print("Initializing, ", cmp.componentname, ":", cmp.componentinstancenumber)

  def print_components(self):
    for itemkey in self.components:
      cmp = self.components[itemkey]
      print(f"I am {cmp.componentname}.{cmp.componentinstancenumber}")
      for i in cmp.connectors:
        connectedcmp = cmp.connectors[i]
        for p in connectedcmp:
          print(f"\t{i} {p.componentname}.{p.componentinstancenumber}")

  def get_non_channel_components(self):
    res = []
    for itemkey in self.components:
      cmp = self.components[itemkey]
      if cmp.componentname.find("Channel") != -1:
        continue
      res.append(cmp)
    return res



class Topology:
  nodes = {}
  channels = {}


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
      cc = nodetype(nodetype.__name__, i)
      self.nodes[i] = cc


  def construct_from_graph(self, G: nx.Graph, nodetype, channeltype, context=None):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)
    for i in nodes:
      cc = nodetype(nodetype.__name__, i)
      self.nodes[i] = cc
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  def construct_single_node(self, nodetype, instancenumber):
    self.singlenode = nodetype(nodetype.__name__, instancenumber)
    self.G = nx.Graph()
    self.G.add_nodes_from([0])
    self.nodes[0] = self.singlenode

  def construct_sender_receiver(self, sendertype, receivertype, channeltype):
    self.sender = sendertype(sendertype.__name__, 0)
    self.receiver = receivertype(receivertype.__name__, 1)
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
    self.nodecolors = ['b'] * N
    self.lock = Lock()
    ComponentRegistry().init()

  def compute_forwarding_table(self):
    # N = len(self.G.nodes)
    self.ForwardingTable = dict(nx.all_pairs_shortest_path(self.G))
    # print(f"There are {N} nodes")
    # for i in range(N):
      # for j in range(N):
        # try:
          # mypath = path[i][j]
          # print(f"{i}to{j} path = {path[i][j]} nexthop = {path[i][j][1]}")
          # self.ForwardingTable[i][j] = path[i][j][1]

          # print(f"{i}to{j}path = NONE")
          # self.ForwardingTable[i][j] = inf  # No paths
        # except IndexError:
          # print(f"{i}to{j} nexthop = NONE")
          # self.ForwardingTable[i][j] = i  # There is a path but length = 1 (self)

  # all-seeing eye routing table contruction
  # def print_forwarding_table(self):
  #   registry.print_components()
  #   print('\n'.join([''.join(['{:4}'.format(item) for item in row])
  #                    for row in list(self.ForwardingTable.values())]))

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
