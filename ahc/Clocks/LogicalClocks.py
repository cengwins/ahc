import random 
import time 
from datetime import datetime
from enum import Enum 


import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph

from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes, Topology


class LogicalClockEventTypes(Enum): 
  INTERNAL = "internal"
  SEND = "senddown"

class LogicalClockMessageTypes(Enum):
  LCM = "LogicalClockMessage"

class LogicalClockMessageHeader(GenericMessageHeader):
  pass 


class LogicalClockMessagePayload(GenericMessagePayload):
  pass 


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
      #increment the counter before sending
      self.counter +=1
      neighbors = Topology().get_neighbors(self.componentinstancenumber)
      destination = neighbors[random.randint(0, len(neighbors)-1)]
      hdr = LogicalClockMessageHeader(LogicalClockMessageTypes.LCM, self.componentinstancenumber, destination)
      payload = LogicalClockMessagePayload(self.counter)
      message = GenericMessage(hdr, payload)
      time.sleep(random.randint(0, 2))
      self.send_down(Event(self, EventTypes.MFRT, message))

      print(f"Messaage sent from node {self.local_time(self.counter)} to node {destination}\n")


  #this should serve as the on_receive
  def on_message_from_bottom(self, eventobj: Event): 
    #after receiving a message you should increment the counter 
    #do some demultiplexing 
    msg = eventobj.eventcontent
    hdr = msg.header 
    payload = msg.payload
    incomingtimestamp = payload.messagepayload
    #update the timer of the payload 
    payload = incomingtimestamp
    self.counter = self.update_timestamp(incomingtimestamp, self.counter)

    print(f"Messaage received at node {self.local_time(self.counter)} from node {hdr.messagefrom}\n")

    self.send_up(Event(self, EventTypes.MFRB, payload))


  def on_internal(self, eventobj: Event): 
    #Increment counter so that we know something happened
    self.counter +=1 
    print(f"Internal event at node {self.local_time(self.counter)}\n")
    randomnumber = random.randint(0,1)
    if randomnumber == 0: 
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    else: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))


  def local_time(self, counter): 
     return f"{self.componentinstancenumber} LOGICAL_TIME = {counter}"


  def update_timestamp(self, recv_time_stamp, counter):
    counter = max(recv_time_stamp, counter)+1
    return counter 


  def __init__(self, componentname, componentinstancenumber): 
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[LogicalClockEventTypes.INTERNAL] = self.on_internal
    self.eventhandlers[LogicalClockEventTypes.SEND] = self.senddown


#IMPLEMENTATION OF VECTOR CLOCKS
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
    self.update_counter()
    neighbors = Topology().get_neighbors(self.componentinstancenumber)
    destination = neighbors[random.randint(0, len(neighbors)-1)]
    hdr = LogicalClockMessageHeader(LogicalClockMessageTypes.LCM, self.componentinstancenumber, destination)
    messagepayload = self.counter[:]
    payload = LogicalClockMessagePayload(messagepayload)
    message = GenericMessage(hdr, payload)
    time.sleep(random.randint(0,2))
    self.send_down(Event(self, EventTypes.MFRT, message))

    print(f"Messaage sent from node {self.local_time(self.counter)} to node {destination}\n") 


  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    incomingtimestamps = payload.messagepayload

    #Adjust your timestamps
    self.update_counter()
    self.update_timestamp(incomingtimestamps, self.counter)
    self.send_up(Event(self, EventTypes.MFRB, None))

    print(f"Messaage received at node {self.local_time(self.counter)} from node {hdr.messagefrom}\n")


  def on_internal(self, eventobj: Event):
    self.update_counter()
    print(f"Internal event at node {self.local_time(self.counter)}\n")

    randomnumber = random.randint(0,1)
    if randomnumber == 0: 
      time.sleep(random.randint(0,2))
      self.send_self(Event(self, LogicalClockEventTypes.INTERNAL, None))
    else: 
      self.send_self(Event(self, LogicalClockEventTypes.SEND, None))

    #randomly decide whether to haev an internal or senddown event
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











