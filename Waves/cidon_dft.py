#!/usr/bin/env python

__author__ = "One solo developer"
__authors__ = ["Mahmoud Alasmar"]
__contact__ = "mahmoud.asmar@metu.edu.tr"
__date__ = "2021/05/26"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"


import random
import time
from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer


registry = ComponentRegistry()
topo = Topology()
source = 0

class ApplicationLayerMessageTypes(Enum):
  START = "START"
  TOKEN = "TOKEN"
  VISITED = "VISITED"

class NodeState(Enum):
  IDLE = "IDLE"
  DISCOVERED = "DISCOVERED"

class NodeMark(Enum):
  visited = "visited"
  unvisited = "unvisited"
  father = "father"
  son = "son"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class ApplicationLayerComponent_Cidon(ComponentModel):
  #mark = {}
  #NeighbourList = {}

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    if self.componentinstancenumber == source:
      destination = self.componentinstancenumber
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.START, self.componentinstancenumber,
                                          destination)
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr, payload)
      self.send_self(Event(self, "start", proposalmessage))
    else:
      pass

  def on_message_from_bottom(self, eventobj: Event):
    try:
      applmessage = eventobj.eventcontent
      hdr = applmessage.header
      if hdr.messagetype == ApplicationLayerMessageTypes.START:
        #print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "start", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.TOKEN:
        #print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "token", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.VISITED:
        #print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "visited", applmessage))
    except AttributeError:
      print("Attribute Error")

  def on_start(self, eventobj: Event):
    if self.state == NodeState.IDLE:
      self.state = NodeState.DISCOVERED
      self.Search()
      for i in self.NeighbourList:
        if self.mark[i] == NodeMark.visited or self.mark[i] == NodeMark.unvisited:
          hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.VISITED, self.componentinstancenumber,
                                                  i)
          payload = ApplicationLayerMessagePayload("23")
          proposalmessage = GenericMessage(hdr_new, payload)
          self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
          self.numMesg += 1


  def on_token(self, eventobj: Event):
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    source = hdr.messagefrom
    if self.state == NodeState.IDLE:
      self.mark[source] = NodeMark.father
      self.state = NodeState.DISCOVERED
      self.Search()
      for i in self.NeighbourList:
        if self.mark[i] == NodeMark.visited or self.mark[i] == NodeMark.unvisited:
          hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.VISITED, self.componentinstancenumber,
                                                  i)
          payload = ApplicationLayerMessagePayload("23")
          proposalmessage = GenericMessage(hdr_new, payload)
          self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
          self.numMesg += 1
    else:
      if self.mark[source] == NodeMark.unvisited:
        self.mark[source] = NodeMark.visited
      elif self.mark[source] == NodeMark.son:
        self.Search()


  def on_visited(self, eventobj: Event):
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    source = hdr.messagefrom
    if self.mark[source] == NodeMark.unvisited:
      self.mark[source] = NodeMark.visited
    elif self.mark[source] == NodeMark.son:
      self.mark[source] = NodeMark.visited
      self.Search()

  def Search(self):
    for i in self.NeighbourList:
      if self.mark[i] == NodeMark.unvisited:
        hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.TOKEN, self.componentinstancenumber,
                                                i)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr_new, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
        self.numMesg += 1
        self.mark[i] = NodeMark.son
        return
      else:
        pass
    if self.componentinstancenumber == source:
      print(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
      print(f"Node-{self.componentinstancenumber} says all nodes were discovered, algorithm is finished")
      pass #  terminate application
    else:
      for i in self.NeighbourList:
        if self.mark[i] == NodeMark.father:
          hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.TOKEN, self.componentinstancenumber,
                                                  i)
          payload = ApplicationLayerMessagePayload("23")
          proposalmessage = GenericMessage(hdr_new, payload)
          self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
          self.numMesg += 1
          print(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
          return

  def __init__(self, componentname, componentinstancenumber,neighbour_list):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["start"] = self.on_start
    self.eventhandlers["token"] = self.on_token
    self.eventhandlers["visited"] = self.on_visited
    self.NeighbourList = neighbour_list
    self.state = NodeState.IDLE
    self.mark = {}
    for i in self.NeighbourList:
      self.mark[i] = NodeMark.unvisited
    self.numMesg  = 0



class AdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
      print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
      self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
      self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
      # SUBCOMPONENTS
      self.neighbour_list = topo.get_neighbors(componentid)
      self.appllayer = ApplicationLayerComponent_Cidon("ApplicationLayer", componentid,self.neighbour_list)
      self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
      self.linklayer = LinkLayer("LinkLayer", componentid)

      # CONNECTIONS AMONG SUBCOMPONENTS
      self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
      self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

      # Connect the bottom component to the composite component....
      self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
      self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

      super().__init__(componentname, componentid)



def main():
  G = nx.Graph()
  """
  for i in range(5):
    G.add_node(i)

  G.add_edge(0, 1)
  G.add_edge(0, 3)
  G.add_edge(0, 4)
  G.add_edge(1, 2)
  G.add_edge(1, 3)
  G.add_edge(1, 4)
  G.add_edge(2, 1)
  G.add_edge(2, 4)
  G.add_edge(2, 3)
  G.add_edge(3, 1)
  G.add_edge(3, 0)
  G.add_edge(3, 2)
"""
  G = nx.random_geometric_graph(6, 0.5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()

  topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)

  # topo is defined as a global variable
  topo.start()

  plt.show()  # while (True): pass

if __name__ == "__main__":
  main()