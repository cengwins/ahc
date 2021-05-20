import os
import sys
import time
import json
import random
import networkx as nx
from enum import Enum
import matplotlib.pyplot as plt

from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Ahc import (ComponentModel, Event, ConnectorTypes, Topology,
                 ComponentRegistry, GenericMessagePayload, GenericMessageHeader,
                 GenericMessage, EventTypes)

registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageTypes(Enum):
  PROPOSE = "PROPOSE"
  ACCEPT = "ACCEPT"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class ApplicationLayerComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    print(self.context)

    
    if self.componentinstancenumber == 0:
      print("HEEYOOOOO!!!", flush=True)
      # destination = random.randint(len(Topology.G.nodes))
      destination = 1
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber,
                                          destination)
      payload = ApplicationLayerMessagePayload("23")
      proposalmessage = GenericMessage(hdr, payload)
      randdelay = random.randint(0, 5)
      #time.sleep(randdelay)
      self.send_self(Event(self, "propose", proposalmessage))
    elif self.componentinstancenumber == 1:
        #time.sleep(1)
        pass
    else:
      pass

  def on_message_from_bottom(self, eventobj: Event):
    try:
      applmessage = eventobj.eventcontent
      hdr = applmessage.header
      if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
    except AttributeError:
      print("Attribute Error")

  # print(f"{self.componentname}.{self.componentinstancenumber}: Gotton message {eventobj.content} ")
  # value = eventobj.content.value
  # value += 1
  # newmsg = MessageContent( value )
  # myevent = Event( self, "agree", newmsg )
  # self.trigger_event(myevent)

  def on_propose(self, eventobj: Event):
    destination = 1
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber, destination)
    payload = ApplicationLayerMessagePayload("23")
    proposalmessage = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, proposalmessage))

  def on_agree(self, eventobj: Event):
    print(f"Agreed on {eventobj.eventcontent}")

  def on_timer_expired(self, eventobj: Event):
    pass

  def __init__(self, componentname, componentinstancenumber, context):
    self.context = context
    super().__init__(componentname, componentinstancenumber, context=context)
    self.eventhandlers["propose"] = self.on_propose
    self.eventhandlers["agree"] = self.on_agree
    self.eventhandlers["timerexpired"] = self.on_timer_expired

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid, context):
    self.context = context
    # SUBCOMPONENTS
    self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid, context=self.context)
    self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
    self.linklayer = LinkLayer("LinkLayer", componentid)
    # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, componentid, context=self.context)