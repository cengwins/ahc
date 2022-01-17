#!/usr/bin/env python

__author__ = "One solo developer"
__authors__ = ["Mahmoud Alasmar"]
__contact__ = "mahmoud.asmar@metu.edu.tr"
__date__ = "2021/05/26"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"



from enum import Enum
from ahc.Ahc import ComponentModel, Event
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Ahc import Topology


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

topo = Topology()

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
    self.NeighbourList = topo.get_neighbors(self.componentinstancenumber)
    self.state = NodeState.IDLE
    self.mark = {}
    for i in self.NeighbourList:
      self.mark[i] = NodeMark.unvisited
    self.numMesg  = 0

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

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["start"] = self.on_start
    self.eventhandlers["token"] = self.on_token
    self.eventhandlers["visited"] = self.on_visited


