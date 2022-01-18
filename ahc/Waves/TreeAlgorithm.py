#!/usr/bin/env python
import time
from ahc.Ahc import *
from itertools import chain

def startTreeAlgorithm(treeTopology):
  for node in treeTopology.nodes.values():
    node.startTreeAlgorithm()

class TreeNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_bottom(self, eventobj: Event):
    for ch in self.unvisitedNeighbours:
      # print(f"EventSource: {eventobj.eventsource} Channel Conns: {chain(*ch.connectors.values())}")
      if eventobj.eventsource in chain(*ch.connectors.values()):
        channel = ch
        break
 
    self.unvisitedNeighbours.remove(channel)
    # self.parent = eventobj.eventsource
    if len(self.unvisitedNeighbours) == 0:
      self.decide()
    elif len(self.unvisitedNeighbours) == 1:
      self.parent = self.unvisitedNeighbours[0]
      print(f"{self.componentname}.{self.componentinstancenumber} sends message to {self.parent.componentname}.{self.parent.componentinstancenumber}")
      self.parent.trigger_event(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    else:
      #do nothing
      pass

  def startTreeAlgorithm(self):
    self.unvisitedNeighbours = self.connectors[ConnectorTypes.DOWN]
    # print(f"{self.componentname}.{self.componentinstancenumber} Neighbours: {self.unvisitedNeighbours}")

    if len(self.connectors[ConnectorTypes.DOWN]) == 1:
      self.parent = self.unvisitedNeighbours[0]
      print(f"{self.componentname}.{self.componentinstancenumber} sends message to {self.parent.componentname}.{self.parent.componentinstancenumber}")
      self.send_down(Event(self, EventTypes.MFRT, None))
      self.unvisitedNeighbours = []

  def decide(self):
    print(f"{self.componentname}.{self.componentinstancenumber} decides.")
    print(f"End Time: {time.time()}")

