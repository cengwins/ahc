import random 
import time 
from datetime import datetime
from enum import Enum 


import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv
import threading 

from Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes, Topology

from Clocks.compression import *


class LogicalClockEventTypes(Enum): 
  INTERNAL = "internal"
  SEND = "senddown"

class LogicalClockMessageTypes(Enum):
  LCM = "LogicalClockMessage"

class LogicalClockMessageHeader(GenericMessageHeader):
  pass 

class LogicalClockMessagePayload(GenericMessagePayload):
  pass 

############################################### LAMPORT CLOCK #################################################################

class LogicalClock(ComponentModel): 
  def on_init(self, eventobj: Event): 
    self.counter = 0 

    if self.componentinstancenumber == 0: 
      self.send_self(Event(self, EventTypes.MFRT, None))

  #this should serve as the on_send  
  def on_message_from_top(self, eventobj: Event): 
    randomnumber = random.randint(0,1)

    if randomnumber == 0: 
      #perfrom an internalEvent
      time.sleep(random.randint(0, 2))
      self.send_self((Event(self, LogicalClockEventTypes.INTERNAL, None)))
    else: 
      #send it to a random neighbour
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))

  def senddown(self, eventobj: Event): 
      self.counter +=1
      neighbors = Topology().get_neighbors(self.componentinstancenumber)
      destination = neighbors[random.randint(0, len(neighbors)-1)]
      hdr = LogicalClockMessageHeader(LogicalClockMessageTypes.LCM, self.componentinstancenumber, destination)
      payload = LogicalClockMessagePayload(self.counter)
      message = GenericMessage(hdr, payload)
      time.sleep(random.randint(1, 3))
      self.send_down(Event(self, EventTypes.MFRT, message))

      print(f"Messaage sent from node {self.local_time(self.counter)} to {destination}\n")


  # This should serve as the on_receive
  def on_message_from_bottom(self, eventobj: Event): 
    #do some demultiplexing 
    msg = eventobj.eventcontent
    hdr = msg.header 
    payload = msg.payload
    incomingtimestamp = payload.messagepayload
    #update the timer of the payload 
    payload = incomingtimestamp
    self.counter = self.update_timestamp(incomingtimestamp, self.counter)

    print(f"Messaage received at node {self.local_time(self.counter)} from {hdr.messagefrom}\n")

    self.send_up(Event(self, EventTypes.MFRB, payload))


  def on_internal(self, eventobj: Event): 
    # Increment counter so that we know something happened
    self.counter +=1 
    print(f"Internal event at node {self.local_time(self.counter)}\n")

    randomnumber = random.randint(0,1)
    if randomnumber == 0: 
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    else: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))


  def local_time(self, counter): 
     return f"{self.componentinstancenumber} LOGICAL_TIME = {counter}, LOCAL_TIME = {datetime.now().time()}"


  def update_timestamp(self, recv_time_stamp, counter):
    counter = max(recv_time_stamp, counter)+1
    return counter 


  def __init__(self, componentname, componentinstancenumber): 
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[LogicalClockEventTypes.INTERNAL] = self.on_internal
    self.eventhandlers[LogicalClockEventTypes.SEND] = self.senddown


############################################### VECTOR CLOCK #################################################################

class VectorClock(LogicalClock):
  def on_init(self, eventobj: Event): 
    N = len(Topology().nodes)
    self.counter = [0] * N

    if self.componentinstancenumber == 0: 
      self.send_self(Event(self, EventTypes.MFRT, None))
    else: 
      pass


  def on_message_from_top(self, eventobj: Event): 
    randomnumber = random.randint(0, 1)

    if randomnumber == 0: 
      time.sleep(random.randint(0, 2))
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    elif randomnumber ==1: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))
  

  def senddown(self, eventobj: Event): 
    self.counter[self.componentinstancenumber] +=1
    neighbors = Topology().get_neighbors(self.componentinstancenumber)
    destination = neighbors[random.randint(0, len(neighbors)-1)]
    hdr = LogicalClockMessageHeader(LogicalClockMessageTypes.LCM, self.componentinstancenumber, destination)
    messagepayload = self.counter[:]
    payload = LogicalClockMessagePayload(messagepayload)
    message = GenericMessage(hdr, payload)
    time.sleep(random.randint(0,2))
    self.send_down(Event(self, EventTypes.MFRT, message))

    print(f"Messaage sent from node {self.local_time(self.counter)} to {destination}\n") 


  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    incomingtimestamps = payload.messagepayload

    #Adjust your timestamps
    self.counter[self.componentinstancenumber] +=1
    self.update_timestamp(incomingtimestamps, self.counter)
    self.send_up(Event(self, EventTypes.MFRB, None))

    print(f"Messaage received at node {self.local_time(self.counter)} from {hdr.messagefrom}\n")


  def on_internal(self, eventobj: Event):
    self.counter[self.componentinstancenumber] +=1
    print(f"Internal event at node {self.local_time(self.counter)}\n")

    randomnumber = random.randint(0,1)
    if randomnumber == 0: 
      time.sleep(random.randint(0,2))
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    else: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))

    # Randomly decide whether to have an internal or send event
    self.send_self(Event(self, LogicalClockEventTypes.SEND, None))


  def update_timestamp(self, incoming_time_stamp, my_time_stamp): 
    for i in range(len(my_time_stamp)): 
      my_time_stamp[i] = max(incoming_time_stamp[i], my_time_stamp[i])
  
    self.counter = my_time_stamp


  def update_counter(self): 
    self.counter[self.componentinstancenumber] +=1


  def __init__(self, componentname, componentinstancenumber): 
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[LogicalClockEventTypes.INTERNAL] = self.on_internal
    self.eventhandlers[LogicalClockEventTypes.SEND] = self.senddown
    self.counter = []


###################################### DIFFERENT CLOCK IMPLEMENTATIONS USING GRAPHS ######################################

#######################################  ASSUMING BOTH N KNOWN AND M UNKNOWN  #######################################

class SuccinctClock(LogicalClock):
  maxevents = 5

  def on_init(self, eventobj: Event): 
    self.counter = 0
    self.graph = nx.DiGraph() 
    self.localGraph = nx.DiGraph()

    if self.componentinstancenumber == 0: 
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))

  # This should serve as the on_send  
  def on_message_from_top(self, eventobj: Event): 
      randomnumber = random.randint(0,1)

      if randomnumber == 0: 
      # Perfrom an internalEvent
        self.send_self((Event(self, LogicalClockEventTypes.INTERNAL, None)))
      else: 
      # Send it to a random neighbor
        self.send_self(Event(self, LogicalClockEventTypes.SEND, None))

  
  def senddown(self, eventobj: Event): 
    # Increment the counter before sending
    self.counter +=1
    self.update_graph(self.counter)
    neighbors = Topology().get_neighbors(self.componentinstancenumber)
    destination = neighbors[random.randint(0, len(neighbors)-1)]
    hdr = LogicalClockMessageHeader(LogicalClockMessageTypes.LCM, self.componentinstancenumber, destination)
    
    # Send the graph, 
    graph_copy = self.graph.copy()
    graph2_copy = self.localGraph.copy()
    encodedGraph = self.prepare_graph(self.counter, graph_copy, graph2_copy)
    payload = LogicalClockMessagePayload(encodedGraph)
    message = GenericMessage(hdr, payload)
    time.sleep(random.randint(1, 3))
    self.send_down(Event(self, EventTypes.MFRT, message))
    
    print(f"Messaage sent from node {self.local_time(self.counter)} to {destination}\n")

    if (self.counter == self.maxevents):
      self.print_me()


  # This should serve as the on_receive
  def on_message_from_bottom(self, eventobj: Event): 
    self.counter +=1
    self.update_graph(self.counter)
    #do some demultiplexing 
    msg = eventobj.eventcontent
    hdr = msg.header 
    payload = msg.payload
    encodedGraph = payload.messagepayload
    decodedGraph = self.decode_graph(encodedGraph, self.counter)
    self.send_up(Event(self, EventTypes.MFRB, None))

    print(f"Messaage received at node {self.local_time(self.counter)} from {hdr.messagefrom}\n")

    if (self.counter == self.maxevents):
      self.print_me()

  def on_internal(self, eventobj: Event): 
    self.counter +=1 
    self.update_graph( self.counter)

    print(f"Internal event at node {self.local_time(self.counter)}\n")
    
    randomnumber = random.randint(0,1)

    if randomnumber == 0: 
      time.sleep(random.randint(1, 3))
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    else: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))

    if (self.counter == self.maxevents):
      self.print_me()

  def update_graph(self, counter):
    if counter == 1: 
      self.localGraph.add_node(self.componentinstancenumber*self.maxevents + counter)
    else: 
     endnodes = [n for n, d in self.localGraph.out_degree() if d == 0]
     self.localGraph.add_edge(endnodes[0], str(self.componentinstancenumber*self.maxevents + counter)) 


  def prepare_graph(self, counter, graph, graph2): 
    if graph.order() == 0:
      graph.add_edges_from(graph2.edges())
    else :
      endNodes = [n for n, d in graph.out_degree() if d == 0]
      graph.add_edges_from(graph2.edges())

    return encode_n(graph, self.maxevents * len(Topology().nodes))


  def decode_graph(self, encodedGraph, counter): 
    decodedGraph = decode_n(encodedGraph, self.maxevents * len(Topology().nodes))
    endnodes = [n for n, d in decodedGraph.out_degree() if d == 0]
    self.graph.add_edges_from(decodedGraph.edges)
    self.graph.add_edge(endnodes[0], self.componentinstancenumber*self.maxevents + counter) 

    return decodedGraph

  def print_me(self):
    combined_graph = nx.DiGraph()
    combined_graph.add_edges_from(self.graph.edges)
    combined_graph.add_edges_from(self.localGraph.edges)

    print(f"Combined_graph at node {self.componentinstancenumber} with {combined_graph.order()} nodes and {combined_graph.number_of_edges()} edges")
    
    A = to_agraph(combined_graph)
    A.layout("dot")
    A.draw("node" +str(self.componentinstancenumber)+".png")
    self.terminate()

  def setMaxEvents(self, maaxEvents): 
    self.maxevents = maaxEvents

#######################################  ASSUMING BOTH N AND M UNKNOWN  #######################################

class SuccinctClock2(SuccinctClock):
  def update_graph(self, counter):
    if counter == 1: 
      self.localGraph.add_node(self.componentinstancenumber*self.maxevents + counter)
    else: 
     endnodes = [n for n, d in self.localGraph.out_degree() if d == 0]
     self.localGraph.add_edge(endnodes[0], (self.componentinstancenumber*self.maxevents + counter)) 


  def prepare_graph(self, counter, graph, graph2): 
    if graph.order() == 0:
      graph.add_edges_from(graph2.edges())
    else:
      endNodes = [n for n, d in graph.out_degree() if d == 0]
      graph.add_edges_from(graph2.edges())

    return encode(graph)


  def decode_graph(self, encodedGraph, counter): 
    decodedGraph = decode(encodedGraph)
    endnodes = [n for n, d in decodedGraph.out_degree() if d == 0]

    self.graph.add_edges_from(decodedGraph.edges)
    self.graph.add_edge(endnodes[0], (self.componentinstancenumber*self.maxevents) + counter) 

    return decodedGraph


############################################### ACTUAL SGLC - BOTH M AND N KNOWN #################################################################

class SuccinctClock3(SuccinctClock):
    
  def on_message_from_bottom(self, eventobj: Event): 
    self.counter = self.counter + 1
    self.update_graph(self.counter)
    # Perfom some demultiplexing 
    msg = eventobj.eventcontent
    hdr = msg.header 
    payload = msg.payload
    [m, tot] = payload.messagepayload
    decodedGraph = self.decode_graph(m, tot, self.counter)
    self.send_up(Event(self, EventTypes.MFRB, None))
    
    if (self.counter >= self.maxevents):
      self.print_me()
 
    print(f"Messaage received at node {self.local_time(self.counter)} from {hdr.messagefrom}")
 
  
  def update_graph(self, counter):
    if counter == 1: 
      self.localGraph.add_node((self.componentinstancenumber*self.maxevents) + counter)
    else: 
     endnodes = [n for n, d in self.localGraph.out_degree() if d == 0]
     self.localGraph.add_edge(endnodes[0], (self.componentinstancenumber*self.maxevents) + counter) 

  def prepare_graph(self, counter, graph, graph2): 
    if graph.order() == 0:
      graph.add_edges_from(graph2.edges())
    else :
      endNodes = [n for n, d in graph.out_degree() if d == 0]
      graph.add_edges_from(graph2.edges())
    
    [m, tot] = encode_nm(graph)
    return [m, tot]


  def decode_graph(self, m, tot, counter): 
    decodedGraph = decode_nm(tot, m)
    endnodes = [n for n, d in decodedGraph.out_degree() if d == 0]
    self.graph.add_edges_from(decodedGraph.edges)
    self.graph.add_edge(endnodes[0], (self.componentinstancenumber*self.maxevents) + counter) 

    return decodedGraph
