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
number_mesg = 0

class ApplicationLayerMessageTypes(Enum):
  DISCOVER = "DISCOVER"
  RETURN = "RETURN"
  VISITED = "VISITED"
  ACK = "ACK"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class ApplicationLayerComponent_Awerbuch(ComponentModel):
  #number_mesg = 0
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    if self.componentinstancenumber == 0:
      destination = self.componentinstancenumber
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.DISCOVER, self.componentinstancenumber,
                                          destination)
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr, payload)
      self.send_self(Event(self, "discover", proposalmessage))
    else:
      pass

  def on_message_from_bottom(self, eventobj: Event):
    try:
      applmessage = eventobj.eventcontent
      hdr = applmessage.header
      if hdr.messagetype == ApplicationLayerMessageTypes.DISCOVER:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "discover", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.VISITED:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "visited", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.RETURN:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "return", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.ACK:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "ack", applmessage))
    except AttributeError:
      print("Attribute Error")

  def on_discover(self, eventobj: Event):
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    self.father = hdr.messagefrom
    for i in self.NeighbourList:
      if i != self.father:
        self.flag[i] = 1
        hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.VISITED, self.componentinstancenumber,i)
        payload = ApplicationLayerMessagePayload("23")  # payload is redundant
        proposalmessage = GenericMessage(hdr_new, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
        self.numMesg+=1
      else:
        pass

    if len(self.NeighbourList) == 1 and self.NeighbourList[0] == self.father:
      hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.RETURN, self.componentinstancenumber,
                                              self.NeighbourList[0])
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr_new, payload)
      self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
      self.numMesg += 1



  def on_return(self, eventobj: Event):

    if not self.Unvisited:
      if self.father != self.componentinstancenumber:
        hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.RETURN, self.componentinstancenumber,
                                                self.father)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr_new, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
        self.numMesg += 1
        print(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
      else:
        print(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
        print(f"I am Node-{self.componentinstancenumber}, algorithm is finished ")

    else:
      destination = random.choice(self.Unvisited)
      hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.DISCOVER, self.componentinstancenumber,
                                              destination)
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr_new, payload)
      self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
      self.numMesg += 1
      self.Unvisited.remove(destination)
      print(f"I am Node-{self.componentinstancenumber} sending DISCOVER to {destination}")

  def on_visited(self, eventobj: Event):
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    k = hdr.messagefrom
    self.Unvisited.remove(k)
    hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACK, self.componentinstancenumber, k)
    payload = ApplicationLayerMessagePayload("23")
    proposalmessage = GenericMessage(hdr_new, payload)
    self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
    self.numMesg += 1


  def on_ack(self, eventobj: Event):
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    k = hdr.messagefrom
    self.flag[k] = 0
    cnt = 0
    for i in self.NeighbourList:
      cnt+=self.flag[i]

    if cnt == 0:
      self.send_self(Event(self, "return", applmessage))
    else:
      pass




  def __init__(self, componentname, componentinstancenumber,neighbour_list):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["discover"] = self.on_discover
    self.eventhandlers["return"] = self.on_return
    self.eventhandlers["visited"] = self.on_visited
    self.eventhandlers["ack"] = self.on_ack
    self.NeighbourList = neighbour_list
    self.Unvisited = neighbour_list.copy()
    self.father = componentinstancenumber
    self.flag = {}
    for i in self.NeighbourList:
      self.flag[i] = 0

    self.numMesg = 0




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
      self.appllayer = ApplicationLayerComponent_Awerbuch("ApplicationLayer", componentid,self.neighbour_list)
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
  """
  G = nx.Graph()
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
  G = nx.random_geometric_graph(50, 0.5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()

  print("Starting Awerbuch test")
  # topo is defined as a global variable
  topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)
  topo.start()


  plt.show()  # while (True): pass

if __name__ == "__main__":
  main()