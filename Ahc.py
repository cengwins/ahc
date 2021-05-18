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
__email__ =  "eonur@ceng.metu.edu.tr"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"


import datetime
import queue
from enum import Enum
from threading import Thread, Lock

import matplotlib.pyplot as plt
import networkx as nx

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

class GenericMessagePayload:
  def __init__(self, messagepayload):
    self.messagepayload = messagepayload

class GenericMessageHeader:
  def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
    self.messagetype = messagetype
    self.messagefrom = messagefrom
    self.messageto = messageto
    self.nexthop = nexthop
    self.interfaceid = interfaceid
    self.sequencenumber = sequencenumber

class GenericMessage:
  def __init__(self, header, payload):
    self.header = header
    self.payload = payload
    self.uniqueid = str(header.messagefrom) + "-" + str(header.sequencenumber)

class Event:
  def __init__(self, eventsource, event, eventcontent, fromchannel=None):
    self.eventsource = eventsource
    self.event = event
    self.time = datetime.datetime.now()
    self.eventcontent = eventcontent
    self.fromchannel = fromchannel

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

  def print_components(self):
    for itemkey in self.components:
      cmp = self.components[itemkey]
      print(f"I am {cmp.componentname}.{cmp.componentinstancenumber}")
      for i in cmp.connectors:
        connectedcmp = cmp.connectors[i]
        for p in connectedcmp:
          print(f"\t{i} {p.componentname}.{p.componentinstancenumber}")

registry = ComponentRegistry()

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

  def __init__(self, componentname, componentinstancenumber, num_worker_threads=1):
    self.eventhandlers = {EventTypes.INIT: self.on_init, EventTypes.MFRB: self.on_message_from_bottom,
                          EventTypes.MFRT: self.on_message_from_top, EventTypes.MFRP: self.on_message_from_peer}
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
    print(f"Connected to channel: {name}:{channel.componentinstancenumber}")

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

  def construct_from_graph(self, G: nx.Graph, nodetype, channeltype):
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
    # registry.printComponents()
    N = len(self.G.nodes)
    self.compute_forwarding_table()
    self.nodecolors = ['b'] * N
    self.nodepos = nx.drawing.spring_layout(self.G)
    self.lock = Lock()
    ComponentRegistry().init()

  def compute_forwarding_table(self):
    #N = len(self.G.nodes)
    self.ForwardingTable = dict(nx.all_pairs_shortest_path(self.G))
    # print(f"There are {N} nodes")
    #for i in range(N):
      #for j in range(N):
        #try:
          #mypath = path[i][j]
          # print(f"{i}to{j} path = {path[i][j]} nexthop = {path[i][j][1]}")
          #self.ForwardingTable[i][j] = path[i][j][1]

          # print(f"{i}to{j}path = NONE")
          #self.ForwardingTable[i][j] = inf  # No paths
        #except IndexError:
          # print(f"{i}to{j} nexthop = NONE")
          #self.ForwardingTable[i][j] = i  # There is a path but length = 1 (self)

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
    #self.lock.acquire()
    nx.draw(self.G, self.nodepos, node_color=self.nodecolors, with_labels=True, font_weight='bold')
    plt.draw()
    print(self.nodecolors)
    #self.lock.release()
