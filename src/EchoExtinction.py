from enum import Enum
from GenericModel import GenericModel
from GenericEvent import GenericEvent
from OSIModel import AdHocNode, P2PFIFOPerfectChannel
from GenericApplicationLayer import GenericApplicationLayer
from generics import *
import time 
import os
import sys
import time
import random
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

from Topology import *


# define your own message types
class ApplicationLayerMessageTypes(Enum):
  PROPOSE = "PROPOSE"
  ACCEPT = "ACCEPT"
  WAVE = "WAVE"
  ACCEPT_WAVE = "ACCEPT_WAVE"
  FINISH_WAVE = "FINISH_WAVE"

#TODO: message_count can be member variable...
message_count = 0
# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class WaveMessagePayload:
  def __init__(self, tag):
    self.tag = tag

topo = Topology()

class XD(GenericApplicationLayer):

  def __init__(self, args):
      super().__init__(args.componentname, args.componentinstancenumber)

  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    self.neighbors = topo.G.neighbors(self.componentinstancenumber)


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

#TODO: If you call this before all on_inits, then things will go wrong...
  def initiate_process(self):
    self.neighbors = topo.G.neighbors(self.componentinstancenumber)
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
          

  def __init__(self, args):
    super().__init__(args['componentname'], args['componentinstancenumber'])

    self.eventhandlers["propose"] = self.on_propose
    self.eventhandlers["agree"] = self.on_agree
    self.eventhandlers["timerexpired"] = self.on_timer_expired
    self.parent = args['componentinstancenumber']
    self.initiated = False
    self.isWaiting = False 

    self.waitingAccepts = []

class Grid:
     def __init__(self, node_count_on_edge: int, ax = None) -> None:
         self.ax = ax
         self.node_count_on_edge = node_count_on_edge
         self.root = random.choice(list(range(self.node_count_on_edge ** 2)))
         self.G = nx.grid_2d_graph(self.node_count_on_edge, self.node_count_on_edge)
         self.positions = {self.node_count_on_edge * x[0] + x[1]: x for x in self.G.nodes()}

         self.G = nx.relabel_nodes(self.G, lambda x: self.node_count_on_edge * x[0] + x[1])

         for u,v in list (self.G.edges):
             self.G[u][v]['weight'] = int(random.random() * 10)

         self.pos = nx.spring_layout(self.G)

     def plot(self):
         node_colors = ["mediumslateblue" for i in range(self.node_count_on_edge ** 2)]

         if self.ax is not None:
             nx.draw(self.G, with_labels=True, node_color=node_colors, pos=self.positions)
             nx.draw_networkx_edge_labels(self.G, pos=self.positions)
         else:
             nx.draw(self.G, self.pos)
             nx.draw_networkx_edge_labels(self.G, self.pos)

def main():
   # G = nx.Graph()
   # G.add_nodes_from([1, 2])
   # G.add_edges_from([(1, 2)])
   # nx.draw(G, with_labels=True, font_weight='bold')
   # plt.draw()
  global message_count
  fig, axes = plt.subplots(1, 7)
  fig.set_figheight(5)
  fig.set_figwidth(10)
  fig.tight_layout()
  time_arr = []
  message_count_arr = []

  

    # for node in self.nodes:
    #   node.replace_component(new, index, args)

  i = 5

  start_time = time.time()

  g = Grid(i, i)
  topo.construct_from_graph(g.G, AdHocNode, P2PFIFOPerfectChannel)
  topo.start()
  nodex = list(topo.G.nodes)
  args = {}
  for i in nodex:
    args['componentinstancenumber'] = topo.nodes[i].componentinstancenumber
    args['componentname'] =  topo.nodes[i].componentname
    topo.nodes[i].replace_component(XD, 4, args)
  for i in range(0,10):
    topo.nodes[i].appllayer.initiate_process()

  end_time = time.time()
  time_arr.append(end_time-start_time)

  message_count_arr.append(message_count)
  message_count = 0 

  g.plot()


  axes[5].plot(np.array([n**2 for n in range(4,9)]), np.array(message_count_arr))  
  axes[6].plot(np.array([n**2 for n in range(4,9)]), np.array(time_arr))
  axes[5].set_ylabel('Messeage Count')
  axes[5].set_xlabel('Node Count')
  axes[6].set_ylabel('Time Passes in Seconds')
  axes[6].set_xlabel('Node Count')
  axes[5].set_title("Message Count by Node Count")
  axes[5].set_title("Time")
  plt.show()
  # plt.show()  # while (True): pass

if __name__ == "__main__":
   main()