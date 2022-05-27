#!/usr/bin/env python
import time


from ...Experimentation.Topology import Topology
from ...GenericModel import GenericModel, GenericMessageHeader, GenericMessagePayload, GenericMessage
from ...Generics import *

from itertools import chain


class TreeNode(GenericModel):

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
      super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)

  def on_init(self, eventobj: Event):
    logger.debug(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_bottom(self, eventobj: Event):
    for ch in self.unvisitedNeighbours:
      # logger.debug(f"EventSource: {eventobj.eventsource} Channel Conns: {chain(*ch.connectors.values())}")
      if eventobj.eventsource in chain(*ch.connectors.values()):
        channel = ch
        break
 
    self.unvisitedNeighbours.remove(channel)
    # self.parent = eventobj.eventsource
    if len(self.unvisitedNeighbours) == 0:
      self.decide()
    elif len(self.unvisitedNeighbours) == 1:
      self.parent = self.unvisitedNeighbours[0]
      logger.debug(f"{self.componentname}.{self.componentinstancenumber} sends message to {self.parent.componentname}.{self.parent.componentinstancenumber}")
      self.parent.trigger_event(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    else:
      #do nothing
      pass

  def startTreeAlgorithm(self):
    self.unvisitedNeighbours = self.connectors[ConnectorTypes.DOWN]
    # logger.debug(f"{self.componentname}.{self.componentinstancenumber} Neighbours: {self.unvisitedNeighbours}")

    if len(self.connectors[ConnectorTypes.DOWN]) == 1:
      self.parent = self.unvisitedNeighbours[0]
      logger.debug(f"{self.componentname}.{self.componentinstancenumber} sends message to {self.parent.componentname}.{self.parent.componentinstancenumber}")
      self.send_down(Event(self, EventTypes.MFRT, None))
      self.unvisitedNeighbours = []

  def decide(self):
    logger.debug(f"{self.componentname}.{self.componentinstancenumber} decides.")
    logger.debug(f"End Time: {time.time()}")

