from random import sample
import itertools
import networkx as nx
from ..Generics import *
#from ..GenericModel import GenericModel
from ..Distribution.LogicalChannelProcess import LogicalChannelProcess
from ..Distribution.NodeProcess import NodeProcess

import queue
from multiprocessing import  Process,Queue,Pipe, JoinableQueue, Manager
import time
import os, sys, signal





inf = float('inf')
class Topology:
  nodes = {}
  channels = {}
  G = None
  nodeproc = [] 
  nodeproc_parent_conn = [] # Pipe ends that will be used by the main thread to communicate with the child SDRNode processes
  chproc = [] 
  chproc_parent_conn = [] # Pipe ends that will be used by the main thread to communicate with the child SDRNode processes

  def __init__(self, name=None) -> None:
#      print("Constructing topology", name)
    pass
  def __getstate__(self):
    return {
      'nodes': self.nodes,
      'channels': self.channels,
      'Graph': self.G,
      'nodeproc': self.nodeproc
    }
  def __setstate__(self, d):
    self.nodes = d['nodes']
    self.channels = d['channels']
    self.G = d['Graph']
    self.nodeproc = d['nodeproc']


  # mp_construct_sdr_topology_without_channels creates separate child processess for nodes without any channels
  # This generator should be used with sdr platforms. Each sdr will be run in a separate process space
  # Note that the classical channel concept will not be applicable, PIPEs will have to be established.
  def mp_construct_sdr_topology_without_channels(self, numnodes, nodetype,context=None):
    print(numnodes)
    for i in range(numnodes):
      parent_conn, child_conn = Pipe()
      p = NodeProcess(nodetype, i, child_conn,None,None)
      self.nodeproc.append(p)
      self.nodeproc_parent_conn.append(parent_conn)
      p.start()


  def mp_construct_sdr_topology(self, G: nx.Graph, nodetype, channeltype, manager, context=None):
    print(G)
    self.G = G
    n = self.G.number_of_nodes()
    nd_queues = [[None for i in range(n)] for j in range(n)]
    ch_queues = [[None for i in range(n)] for j in range(n)]

    for i in range(n):
      for j in range(n):
        src = i
        dest = j
        if src != dest:
          if G.has_edge(src,dest): #symmetric links but there will be a channel process in between to two queues are required so two queues per symmetric channel
            ch_queues[src][dest] = Queue(maxsize=100)
            #ch_queues[src][dest] = manager.get_queue(maxsize=100)
            #print("CQ", src, dest, "will be created", ch_queues[src][dest])
            nd_queues[src][dest] = Queue(maxsize=100)
            #nd_queues[src][dest] = manager.get_queue(maxsize=100)
            #print("NQ", src, dest, " will be created", nd_queues[src][dest])
        #else:
        #  #print(i, j, "EQUAL NO OP")
        #  ch_queues[src][dest] = None
        #  nd_queues[src][dest] = None
    for i in range(n):
      parent_conn, child_conn = Pipe()
      p = NodeProcess(nodetype, i, child_conn, nd_queues, ch_queues)
      p.daemon = True
      self.nodeproc.append(p)
      self.nodeproc_parent_conn.append(parent_conn)
      #p.start()
      for j in range(n):
        src = i
        dest = j
        if src != dest:
          if G.has_edge(src,dest): #symmetric links but there will be a channel process in between to two queues are required
            chname = str(src) + "-" + str(dest)
            ch_parent_conn, ch_child_conn = Pipe()
            c = LogicalChannelProcess(channeltype, chname,ch_child_conn,nd_queues, ch_queues )
            c.daemon = True
            self.chproc.append(c)
            self.chproc_parent_conn.append(ch_parent_conn)
            #c.start()
        else:
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


  def construct_winslab_topology_without_channels_for_docker(self, nodetype, id, context=None):
    
    self.G = nx.Graph()
    self.G.add_nodes_from(range(1))  # TODO : Change depending on the 

    nodes = list(self.G.nodes)
    cc = nodetype(nodetype.__name__, id)
    self.nodes[0] = cc


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
      #print("Channel", ch.componentname)

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
    self.nodes[self.receiver.componentinstancenumber] = self.receiver
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
    try:
      if self.nodeproc is not None:
        for i in range(len(self.nodeproc)):
          self.nodeproc[i].start()
      if self.chproc is not None:
        for i in range(len(self.chproc)):
          self.chproc[i].start()
    except Exception as ex:
      print(ex)
    try:
      if self.G is not None and self.G.nodes is not None:
        N = len(self.G.nodes)
        self.compute_forwarding_table()
        for i in self.G.nodes:
          node = self.nodes[i]
          if node.initeventgenerated == False:
            node.initiate_process()
        for i in self.channels:
          ch = self.channels[i]
          ch.initiate_process()
    except Exception as ex:
      print("Exception in topology.start: ", ex)
    #check and initialize if nodes are created using multiprocessing
    try:
      if self.nodeproc is not None and self.nodeproc_parent_conn is not None:
        init_event = Event(None, EventTypes.INIT, None)
        for i in range(len(self.nodeproc)):
          self.nodeproc_parent_conn[i].send(init_event)
    except Exception as ex:
      print("Exception in topology.start multiprocessing 1: ", ex)
    try:
      if self.chproc is not None and self.chproc_parent_conn is not None:
        init_event = Event(None, EventTypes.INIT, None)
        for i in range(len(self.chproc)):
          self.chproc_parent_conn[i].send(init_event)
    except Exception as ex:
      print("Exception in topology.start multiprocessing 2: ", ex)



  def exit(self):
    try:
      if self.G is not None and self.G.nodes is not None:
        for i in self.G.nodes:
          node = self.nodes[i]
          if node.terminatestarted == False:
            node.exit_process()
            node.terminatestarted = True
        for i in self.channels:
          ch = self.channels[i]
          if ch.terminatestarted == False:
            ch.exit_process()
            ch.terminatestarted = True
    except Exception as ex:
      print("Exception in topology.start: ", ex)
    try:
      if self.nodeproc is not None and self.nodeproc_parent_conn is not None:
        exit_event = Event(None, EventTypes.EXIT, None)
        for i in range(len(self.nodeproc)):
          self.nodeproc_parent_conn[i].send(exit_event)
    except Exception as ex:
      print("Exception in topology.exit multiprocessing: ", ex)
    try:
      if self.chproc is not None and self.chproc_parent_conn is not None:
        exit_event = Event(None, EventTypes.EXIT, None)
        for i in range(len(self.chproc)):
          self.chproc_parent_conn[i].send(exit_event)
    except Exception as ex:
      print("Exception in topology.exit multiprocessing: ", ex)
  
  def compute_forwarding_table(self):
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

