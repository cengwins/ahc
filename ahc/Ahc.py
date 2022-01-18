#!/usr/bin/env python
""" Implements the AHC library.

TODO: Longer description of this module to be written.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = "One solo developer"
__authors__ = ["Ertan Onur", "Berke Tezergil", "etc"]
__contact__ = "eonur@ceng.metu.edu.tr"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Ertan Onur", "Berke Tezergil", "etc"]
__date__ = "2021/04/07"
__deprecated__ = False
__email__ = "eonur@ceng.metu.edu.tr"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"

import datetime
import queue
from enum import Enum
from threading import Thread, Lock
from random import sample, random, sample
import itertools
from matplotlib.pyplot import flag
import networkx as nx
import itertools
import threading
import time
# TIMING ASSUMPTIONS
# TODO: Event handling time, message sending time, assumptions about clock (drift, skew, ...)
# TODO: 1. Asynch,  2. Synch 3. Partial-synch 4. Timed asynch
# TODO: Causal-order (happen before), total-order,
# TODO: Causal-order algebra!!!
# TODO: Implement logical clocks (Lamport clocks, vector clocks) in event handling loop

#  AUTOMATA and EXECUTIONS
# TODO: Let component model hande executions and chekcs on executions (which event, in which order, per process or per system, similarity of executions)

#  VISUALIZATION
# TODO: Space-time diagrams for events

#  TOPOLOGY MANAGEMENT
# TODO: Given a graph as input, generate the topology....

inf = float('inf')


# The following are the common default events for all components.
class EventTypes(Enum):
  INIT = "init"
  MFRB = "msgfrombottom"
  MFRT = "msgfromtop"
  MFRP = "msgfrompeer"


class MessageDestinationIdentifiers(Enum):
  LINKLAYERBROADCAST = -1,  # sinngle-hop broadcast, means all directly connected nodes
  NETWORKLAYERBROADCAST = -2  # For flooding over multiple-hops means all connected nodes to me over one or more links


# A Dictionary that holds a list for the same key
class ConnectorList(dict):

  def __setitem__(self, key, value):
    try:
      self[key]
    except KeyError:
      super(ConnectorList, self).__setitem__(key, [])
    self[key].append(value)


class ConnectorTypes(Enum):
  DOWN = "DOWN"
  UP = "UP"
  PEER = "PEER"


def auto_str(cls):

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


@auto_str
class GenericMessagePayload:

  def __init__(self, messagepayload):
    self.messagepayload = messagepayload


@auto_str
class GenericMessageHeader:

  def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
    self.messagetype = messagetype
    self.messagefrom = messagefrom
    self.messageto = messageto
    self.nexthop = nexthop
    self.interfaceid = interfaceid
    self.sequencenumber = sequencenumber


@auto_str
class GenericMessage:

  def __init__(self, header, payload):
    self.header = header
    self.payload = payload
    self.uniqueid = str(header.messagefrom) + "-" + str(header.sequencenumber)


@auto_str
class Event:
  curr_event_id = 0

  def __init__(self, eventsource, event, eventcontent, fromchannel=None,
               eventid=-1):
    self.eventsource = eventsource
    self.event = event
    self.time = datetime.datetime.now()
    self.eventcontent = eventcontent
    self.fromchannel = fromchannel
    self.eventid = eventid
    if self.eventid == -1:
      self.eventid = self.curr_event_id
      self.curr_event_id += 1

  def __eq__(self, other) -> bool:
    if type(other) is not Event:
      return False

    return self.eventid == other.eventid

  def __hash__(self) -> int:
    return self.eventid


def singleton(cls):
  instance = [None]

  def wrapper(*args, **kwargs):
    if instance[0] is None:
      instance[0] = cls(*args, **kwargs)
    return instance[0]

  return wrapper


@singleton
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
      #print("Initializing, ", cmp.componentname, ":", cmp.componentinstancenumber)

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


registry = ComponentRegistry()

class ComponentConfigurationParameters():
    pass

class ComponentModel:
  terminated = False

  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def on_message_from_bottom(self, eventobj: Event):
    print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_peer(self, eventobj: Event):
    print(f"{EventTypes.MFRP}  {self.componentname}.{self.componentinstancenumber}")

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1):
    self.context = context
    self.configurationparameters = configurationparameters
    self.eventhandlers = {
                          EventTypes.INIT: self.on_init, 
                          EventTypes.MFRB: self.on_message_from_bottom,
                          EventTypes.MFRT: self.on_message_from_top, 
                          EventTypes.MFRP: self.on_message_from_peer
                        }
    # Add default handlers to all instantiated components.
    # If a component overwrites the __init__ method it has to call the super().__init__ method
    self.inputqueue = queue.Queue()
    self.componentname = componentname
    self.componentinstancenumber = componentinstancenumber
    self.num_worker_threads = num_worker_threads
    
    try:
      if self.connectors:
        pass
    except AttributeError:
      self.connectors = ConnectorList()

    self.registry = ComponentRegistry()
    self.registry.add_component(self)

    for i in range(self.num_worker_threads):
      t = Thread(target=self.queue_handler, args=[self.inputqueue])
      t.daemon = True
      t.start()

  def connect_me_to_component(self, name, component):
    try:
      self.connectors[name] = component
    except AttributeError:
      self.connectors = ConnectorList()
      self.connectors[name] = component

  def remove_connection_to_component_from_me(self, name, component):
    try:
      self.connectors[name].remove(component)
    except AttributeError:
      pass

  def remove_connection_to_channel_from_me(self, name, channel):
    try:
      self.connectors[name].remove(channel)
    except AttributeError:
      pass
    connectornameforchannel = self.componentname + str(self.componentinstancenumber)
    channel.remove_connection_to_component_from_me(connectornameforchannel, self)
    self.on_break_connection_to_channel(name, channel)

  def on_break_connection_to_channel(self, name, channel):
    print(f"Connection broken to channel: {name}:{channel.componentinstancenumber}")

  def connect_me_to_channel(self, name, channel):
    try:
      self.connectors[name] = channel
    except AttributeError:
      self.connectors = ConnectorList()
      self.connectors[name] = channel
    connectornameforchannel = self.componentname + str(self.componentinstancenumber)
    channel.connect_me_to_component(connectornameforchannel, self)
    self.on_connected_to_channel(name, channel)

  def on_connected_to_channel(self, name, channel):
    pass
    #print(f"Connected to channel: {name}:{channel.componentinstancenumber}")

  def on_pre_event(self, event):
    pass

  def unique_name(self):
    return f"{self.componentname}.{self.componentinstancenumber}"

  def terminate(self):
    self.terminated = True

  def send_down(self, event: Event):
    try:
      for p in self.connectors[ConnectorTypes.DOWN]:
        p.trigger_event(event)
    except:
      pass

  def send_up(self, event: Event):
    try:
      for p in self.connectors[ConnectorTypes.UP]:
        p.trigger_event(event)
    except:
      pass

  def send_peer(self, event: Event):
    try:
      for p in self.connectors[ConnectorTypes.PEER]:
        p.trigger_event(event)
    except:
      pass

  def send_self(self, event: Event):
    self.trigger_event(event)

  # noinspection PyArgumentList
  def queue_handler(self, myqueue):
    while not self.terminated:
      workitem = myqueue.get()
      if workitem.event in self.eventhandlers:
        self.on_pre_event(workitem)
        self.eventhandlers[workitem.event](eventobj=workitem)  # call the handler
      else:
        print(f"Event Handler: {workitem.event} is not implemented")
      myqueue.task_done()

  def trigger_event(self, eventobj: Event):
    self.inputqueue.put_nowait(eventobj)


@singleton
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


  def construct_winslab_topology_without_channels_for_docker(self, nodetype, id, context=None):
    
    self.G = nx.Graph()
    self.G.add_nodes_from(range(1))  # TODO : Change depending on the 

    nodes = list(self.G.nodes)
    cc = nodetype(nodetype.__name__, id)
    self.nodes[0] = cc
    
  def construct_from_graph_key_exchange(self, G: nx.Graph, nodetype1, nodetype2, nodetype3, channeltype, context=None):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)
    j = 0
    for i in nodes:
      print(i)
      if(j == 0):
        cc = nodetype1(nodetype1.__name__, i)
      elif(j == 1):
        cc = nodetype2(nodetype2.__name__, i)
      else:
        cc = nodetype3(nodetype3.__name__, i)
      self.nodes[i] = cc
      j+=1
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  #def construct_from_graph(self, G: nx.Graph, nodetype, channeltype, context=None):
  def construct_from_graph(self, G: nx.Graph, nodetype, channeltype, context=None, dynamic = False, path = "topology.txt"):
    self.G = G
    nodes = list(G.nodes('conf', None))
    edges = list(G.edges)
    for (i, cf) in nodes:
      if cf is None:
        cc = nodetype(nodetype.__name__, i)
      else:
        cc = nodetype(nodetype.__name__, i, configurationparameters=cf)
      self.nodes[i] = cc
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
    
    if dynamic:
      self.file_path = path
      self._timer_(self.enable_dynamic_topology, nodetype, channeltype)

  def _timer_(self, function, *args):
    stopped = threading.Event()

    def loop():
        while not stopped.wait(random() * 10): # the first call is in `interval` secs
                function(*args)

    threading.Thread(target=loop).start()    
    return stopped.set

  def enable_dynamic_topology(self,
      nodetype,
      channeltype,
      new_node: float = 0.6, # the probability of creating new node
      delete_node: float = 0.4, # the probability of deletion of current nodes
      new_edge: float = 0.45, # the probability of creating new edge
      delete_edge: float = 0.45, # the probability of deletion new edge 
      ) -> None:

      flags = {
        "new_node": random() <= new_node,
        "delete_node": random() <= delete_node,
        "new_edge": random() <= new_edge,
        "delete_edge": random() <= delete_edge
      }

      if flags["new_node"]:
        u = max(self.nodes) + 1
        v = sample(sorted(self.nodes), 1)[0]
        self.G.add_node(u)
        self.G.add_edge(u, v)
        cc = nodetype(nodetype.__name__, u, u)
        self.nodes[u] = cc

        ch = channeltype(channeltype.__name__, str(u) + "-" + str(v))
        self.channels[(u,v)] = ch
        self.nodes[u].connect_me_to_channel(ConnectorTypes.DOWN, ch)
        self.nodes[v].connect_me_to_channel(ConnectorTypes.DOWN, ch)

      # if flags["delete_node"]:
      #   self.G.remove_node(sample(self.nodes, 1)[0])

      if flags["new_edge"]:
        all_possible_edges = list(itertools.combinations(self.nodes.keys(), 2))
        for i in self.channels.keys():
          all_possible_edges.remove((min(i),max(i)))
        u, v = sample(all_possible_edges, 1)[0]

        self.G.add_edge(u, v)
        ch = channeltype(channeltype.__name__, str(u) + "-" + str(v))
        self.channels[(u,v)] = ch
        self.nodes[u].connect_me_to_channel(ConnectorTypes.DOWN, ch)
        self.nodes[v].connect_me_to_channel(ConnectorTypes.DOWN, ch)

      if flags["delete_edge"]:
         u, v = sample(self.channels.keys(), 1)[0]
         node_u = self.nodes[u]
         node_v = self.nodes[v]
         self.G.remove_edge(u, v)
         ch = self.channels[(u,v)]
         node_u.remove_connection_to_channel_from_me(ConnectorTypes.DOWN, ch)
         node_v.remove_connection_to_channel_from_me(ConnectorTypes.DOWN, ch)

      with open(self.file_path, "a") as f:
        f.write(str(time.time_ns() / 1000) + '\n')
        f.write(str(self.G.nodes) + '\n')
        f.write(str(self.G.edges) + '\n')
        f.write('\n')

# TODO: construct_from_graph_peterson and construct_from_graph_bakery will be removed... Does not follow the AHC style..
  def construct_from_graph_peterson(self, G: nx.Graph, nodetype, channeltype):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)

    nodes = nodes[::-1]
    edges = edges[::-1]

    for i in nodes:
      cc = nodetype(nodetype.__name__, i, i)
      self.nodes[i] = cc
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  def construct_from_graph_key_exchange(self, G: nx.Graph, nodetype1, nodetype2, nodetype3, channeltype, context=None):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)
    j = 0
    for i in nodes:
      if(j == 0):
        cc = nodetype1(nodetype1.__name__, i)
      if(j == 1):
        cc = nodetype2(nodetype2.__name__, i)
      else:
        cc = nodetype3(nodetype3.__name__, i)
      self.nodes[i] = cc
      j+=1
    for k in edges:
      ch = channeltype(channeltype.__name__, str(k[0]) + "-" + str(k[1]))
      self.channels[k] = ch
      self.nodes[k[0]].connect_me_to_channel(ConnectorTypes.DOWN, ch)
      self.nodes[k[1]].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  def construct_from_graph_bakery(self, G: nx.Graph, nodetype, channeltype):
    self.G = G
    nodes = list(G.nodes)
    edges = list(G.edges)

    nodes = nodes[::-1]
    edges = edges[::-1]

    for i in nodes:
      cc = nodetype(nodetype.__name__, i, i)
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
    # registry.printComponents()
    N = len(self.G.nodes)
    self.compute_forwarding_table()
    self.nodecolors = ['b'] * N
    # self.nodepos = nx.drawing.spring_layout(self.G)
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
  def print_forwarding_table(self):
    registry.print_components()
    print('\n'.join([''.join(['{:4}'.format(item) for item in row])
                     for row in list(self.ForwardingTable.values())]))

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
    # nx.draw(self.G, self.nodepos, node_color=self.nodecolors, with_labels=True, font_weight='bold')
    # plt.draw()
    print(self.nodecolors)
    # self.lock.release()

  def get_random_node(self):
    return self.nodes[sample(self.G.nodes(), 1)[0]]

@singleton
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



framers = FramerObjects()


