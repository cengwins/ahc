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
from enum import Enum
from ...Experimentation.Topology import Topology
from ...GenericModel import GenericModel, GenericMessageHeader, GenericMessagePayload, GenericMessage
from ...Generics import *

# hocam artik boyle cagirinca topology yi yeni bir class olusuyor ondan dolayi bu tur cagirmalari 
# mainde yaparsaniz daha iyi olabilir kod anlasilabilirligi acisindan 
# topology bilgisini kendi kurdugunuz AdHocNode classina mesela atabilirsiniz topology classini extend ederek vs. 
# Benzer bir neighbor listesini bulmayi GenericNetworkLayer classinda implement ettim oradan bakabilirsiniz 

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

class WaveAwerbuchComponent(GenericModel):
  def on_init(self, eventobj: Event):
    logger.debug(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    neighbour_list = self.topology.get_neighbors(self.componentinstancenumber)
    self.NeighbourList = neighbour_list
    self.Unvisited = neighbour_list.copy()
    self.father = self.componentinstancenumber
    self.flag = {}
    for i in self.NeighbourList:
      self.flag[i] = 0

    self.numMesg = 0

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
        logger.debug(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "discover", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.VISITED:
        logger.debug(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "visited", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.RETURN:
        logger.debug(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "return", applmessage))
      elif hdr.messagetype == ApplicationLayerMessageTypes.ACK:
        logger.debug(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        self.send_self(Event(self, "ack", applmessage))
    except AttributeError:
      logger.error("Attribute Error")

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
        logger.debug(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
      else:
        logger.debug(f"I am Node-{self.componentinstancenumber} local number messages sent is {self.numMesg}")
        logger.debug(f"I am Node-{self.componentinstancenumber}, algorithm is finished ")

    else:
      destination = random.choice(self.Unvisited)
      hdr_new = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.DISCOVER, self.componentinstancenumber,
                                              destination)
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr_new, payload)
      self.send_down(Event(self, EventTypes.MFRT, proposalmessage))
      self.numMesg += 1
      self.Unvisited.remove(destination)
      logger.debug(f"I am Node-{self.componentinstancenumber} sending DISCOVER to {destination}")

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




  def __init__(self, componentname, componentinstancenumber, topology):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["discover"] = self.on_discover
    self.eventhandlers["return"] = self.on_return
    self.eventhandlers["visited"] = self.on_visited
    self.eventhandlers["ack"] = self.on_ack
    self.topology = topology




