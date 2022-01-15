#!/usr/bin/env python
import time
import random
from ahc.Ahc import *
from itertools import chain

#Please close prints if you are working with big graphs for better results.

def startEchoAlgorithm(echoTopology):
  # print(echoTopology.nodes)
  initiator = random.choice(list(echoTopology.nodes.values()))
  initiator.startEchoAlgorithm()

class EchoNode(ComponentModel):

  def __init__(self, componentname, componentid):
    super().__init__(componentname, componentid)
    self.isInitiator = False
    self.isFirstMessage = True

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    
  def on_message_from_bottom(self, eventobj: Event):
    if self.isFirstMessage:
      self.remainingNeighbours = self.connectors[ConnectorTypes.DOWN]      

    for ch in self.remainingNeighbours:
      # print(f"EventSource: {eventobj.eventsource} Channel Conns: {chain(*ch.connectors.values())}")
      if eventobj.eventsource in chain(*ch.connectors.values()):
        channel = ch
        break

    self.remainingNeighbours.remove(channel)

    if self.isFirstMessage:
      for ch in self.remainingNeighbours:
        print(f"{self.componentname}.{self.componentinstancenumber} sends message to {ch.componentname}.{ch.componentinstancenumber}")
        ch.trigger_event(Event(self, EventTypes.MFRT, eventobj.eventcontent))
      self.isFirstMessage = False
      self.parent = channel

    if len(self.remainingNeighbours) == 0:
      print(f"{self.componentname}.{self.componentinstancenumber} has received message from all neighbours.")
      if self.isInitiator:
        self.decide()

      else:
        print(f"{self.componentname}.{self.componentinstancenumber} sends message to parent {self.parent.componentname}.{self.parent.componentinstancenumber}")
        self.parent.trigger_event(Event(self, EventTypes.MFRT, eventobj.eventcontent))
      
    else:
      # print(f"{self.componentname}.{self.componentinstancenumber}: Channel {channel.componentinstancenumber} removed")
      #do nothing
      pass

  def send_down(self, event: Event):
    try:
      for p in self.connectors[ConnectorTypes.DOWN]:
        print(f"{self.componentname}.{self.componentinstancenumber} sends message to {p.componentname}.{p.componentinstancenumber}")
        p.trigger_event(event)
    except:
      pass

  def startEchoAlgorithm(self):
    self.isInitiator = True
    self.isFirstMessage = False
    self.remainingNeighbours = self.connectors[ConnectorTypes.DOWN]      
    print(f"{self.componentname}.{self.componentinstancenumber} is the initiator.")
    
    self.send_down(Event(self, EventTypes.MFRT, None))

  def decide(self):
    print(f"{self.componentname}.{self.componentinstancenumber} decides.")
    print(f"End Time: {time.time()}")
