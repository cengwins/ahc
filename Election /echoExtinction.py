import os
import sys
import time
import random
from enum import Enum
from graph import *
import numpy as np
sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageTypes(Enum):
  PROPOSE = "PROPOSE"
  ACCEPT = "ACCEPT"
  WAVE = "WAVE"
  ACCEPT_WAVE = "ACCEPT_WAVE"
  FINISH_WAVE = "FINISH_WAVE"
  

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class WaveMessagePayload:
  def __init__(self, tag):
    self.tag = tag

class ApplicationLayerComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass
    
    # destination = random.randint(len(Topology.G.nodes))
    # destination = 1
    # hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber, destination)
    # payload = ApplicationLayerMessagePayload("23")
    # proposalmessage = GenericMessage(hdr, payload)
    # randdelay = random.randint(0, 5)
    # time.sleep(randdelay)
    # self.send_self(Event(self, "propose", proposalmessage))

  def on_message_from_bottom(self, eventobj: Event):
    try:
      applmessage = eventobj.eventcontent
      hdr = applmessage.header
      global message_count 
      message_count += 1
      if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      elif hdr.messagetype == ApplicationLayerMessageTypes.WAVE:
        print(f"Node-{self.componentinstancenumber} get message from Node-{hdr.messagefrom} with tag {applmessage.payload.tag}")
        self.wave_message(applmessage.payload, hdr)
      elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT_WAVE:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} is ACCEPT_WAVE")
        self.accept_wave_message(applmessage.payload, hdr)


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

  def initiate_process(self):
    print(f"Process initiated {self.componentinstancenumber}")
    self.initiated = True
    for i in self.neighbors:

      destination = i
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
      payload = WaveMessagePayload(self.componentinstancenumber)
      wave_msg = GenericMessage(hdr, payload)
      self.send_down(Event(self, EventTypes.MFRT, wave_msg))

    
#TO DO WRITE CHECK EVERY  ACCEPT_WAV E MESSAGES CAME OR NOT IN ANOTTHER FUNC

  def accept_wave_message(self, payload, hdr):
    self.waitingAccepts.remove(hdr.messagefrom)
    if len(self.waitingAccepts) == 0:
      destination = self.parent 
      hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
      payload = WaveMessagePayload(self.parent)
      wave_msg = GenericMessage(hdr1, payload)
      self.send_down(Event(self, EventTypes.MFRT, wave_msg))

  def wave_message(self, payload, hdr):
    if self.initiated: 
      if payload.tag  > self.parent: 
        self.isWaiting = True
        self.parent = hdr.messagefrom

        for i in self.neighbors:
          destination = i 
          hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
          wave_msg = GenericMessage(hdr1, payload)
          self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          self.waitingAccepts.append(i)
        
      elif self.parent > payload.tag: 
        print(f"Node-{self.componentinstancenumber} says tag=={payload.tag} from Node-{hdr.messagefrom} is not accepted")
        pass
      else: 
        destination = hdr.messagefrom
        hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
        wave_msg = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, wave_msg))
    else: 
      if self.parent != payload.tag:
        self.parent = hdr.messagefrom
        print(f"Node-{self.componentinstancenumber} has new parent Node-{self.parent}")
        for i in self.neighbors:
          if i == hdr.messagefrom: 
            continue
          destination = i 
          hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
          wave_msg = GenericMessage(hdr1, payload)
          self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          self.waitingAccepts.append(i)
      else: 
        destination = hdr.messagefrom
        hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
        wave_msg = GenericMessage(hdr1, payload)
        self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          

      


  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["propose"] = self.on_propose
    self.eventhandlers["agree"] = self.on_agree
    self.eventhandlers["timerexpired"] = self.on_timer_expired
    self.parent = componentinstancenumber
    self.initiated = False
    self.isWaiting = False 
    self.neighbors = topo.G.neighbors(componentinstancenumber)
    self.waitingAccepts = []

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid)
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
    
    super().__init__(componentname, componentid)
    
  def initiate_process(self):
    self.appllayer.initiate_process()


topo = Topology()

message_count = 0 



def main():
  # G = nx.Graph()
  # G.add_nodes_from([1, 2])
  # G.add_edges_from([(1, 2)])
  # nx.draw(G, with_labels=True, font_weight='bold')
  # plt.draw()
  global message_count
  fig, axes = plt.subplots(1, 2)
  fig.set_figheight(5)
  fig.set_figwidth(10)
  fig.tight_layout()
  time_arr = []
  message_count_arr = []

  for i in range(4, 9):

    start_time = time.time()

    g = Grid(i, ax= axes[0])
    topo.construct_from_graph(g.G, AdHocNode, P2PFIFOPerfectChannel)
    topo.start()
    for i in range(0,10):
      topo.nodes[i].initiate_process()

    end_time = time.time()
    time_arr.append(end_time-start_time)

    message_count_arr.append(message_count)
    message_count = 0 

    # g.plot()


  axes[0].plot(np.array([n**2 for n in range(4,9)]), np.array(message_count_arr))  
  axes[1].plot(np.array([n**2 for n in range(4,9)]), np.array(time_arr))
  axes[0].set_ylabel('Messeage Count')
  axes[0].set_xlabel('Node Count')
  axes[1].set_ylabel('Time Passes in Seconds')
  axes[1].set_xlabel('Node Count')
  axes[0].set_title("Message Count by Node Count")
  axes[1].set_title("Time")
  plt.show()
  # plt.show()  # while (True): pass

if __name__ == "__main__":
  main()