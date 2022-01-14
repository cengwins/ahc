import random as rand
from types import new_class
from typing import List, Set, Tuple
from uuid import uuid4
import time

from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes,Topology

from ahc.Routing.ARA.ARAConfiguration import ARAConfiguration
from ahc.Routing.ARA.ARAEventTypes import ARAEventTypes
from ahc.Routing.ARA.ARARoutingEntry import ARARoutingEntry

"""
  implementation of "ARA-the ant-colony based routing algorithm for MANETs"
  [online] https://www.researchgate.net/publication/3971279_ARA-the_ant-colony_based_routing_algorithm_for_MANETs
"""

class RoutingARAComponent(ComponentModel):
  def __init__(self, componentname, componentid):
    super().__init__(componentname, componentid)

    # Information for ARA algorithm
    self.componentId = componentid
    self.neighbors = [] # the list of neighbors (ids) connected to the node
    self.entryTable: List[ARARoutingEntry] = [] # stores the routing table information
    self.visitedAnts: Set = set() # use set for unique tuples
    self.sequenceNums = []
    self.msgCache = [] # to cache the message and send them when route is found


  def on_init(self, eventobj: Event):
      super(RoutingARAComponent, self).on_init(eventobj)
      self.neighbors = Topology().get_neighbors(self.componentinstancenumber)

  def on_message_from_bottom(self, eventobj: Event):
    if (int(eventobj.eventcontent.header.interfaceid.split("-")[1]) == self.componentId):
      self.ARA(eventobj)

  def ARA(self, eventobj: Event):
    message_target = eventobj.eventcontent.header.messageto.split("-")[0]
    message_target_id = eventobj.eventcontent.header.messageto.split("-")[1]

    if message_target == "RoutingARAComponent":
      # for each message we should evaporate the pheromone value
      for entry in self.entryTable:
        entry.evaporatePheromone()

      message_header = eventobj.eventcontent.header    
      if (message_header.messagetype == ARAEventTypes.REGULAR):
        if (not self.pass_regular_packet(eventobj)):
          self.msgCache.append(eventobj) # cache msg for route found
          forward_ant_message = self.make_ant_packet(self.componentId, message_target_id, ARAEventTypes.FANT)
          self.send_to_neighbors(forward_ant_message)
      elif (message_header.messagetype == ARAEventTypes.FANT):
        self.pass_discovery_ant(eventobj)
      elif (message_header.messagetype == ARAEventTypes.BANT):
        self.pass_discovery_ant(eventobj)
      elif (message_header.messagetype == ARAEventTypes.DUPLICATE_ERROR):
        self.deactivate_loop_route(eventobj)
      elif (message_header.messagetype == ARAEventTypes.ROUTE_ERROR):
        # this case is for dynamic networks, hence we can ignore it
        return
      else :
        print("ERROR Unknown Message Type", message_header.messagetype)

  def pass_regular_packet(self, eventobj: Event) -> bool:
    # check if we are the destination of the packet
    messageto = eventobj.eventcontent.header.messageto.split("-")[1]
    if (self.componentId != int(messageto)):
      entries = self.find_destination_entries(int(messageto))
      
      if(len(entries) == 0):
        return False
      else:
        if (eventobj.eventcontent.header.sequencenumber in self.sequenceNums):
          # means that we have seen this data package and we are in a loop situation for regular packet
          self.pass_loop_packet(eventobj)
        else: 
          self.sequenceNums.append(eventobj.eventcontent.header.sequencenumber)
          next_hop = self.find_next_hop(entries)
          self.send_to_one_neighbor(eventobj.eventcontent, next_hop.nextHopAddress)
          next_hop.increasePheromone()
    else:
      if (int(eventobj.eventcontent.header.messagefrom.split("-")[1]) != self.componentId):
        if (eventobj.eventcontent.header.sequencenumber not in self.sequenceNums):
          self.sequenceNums.append(eventobj.eventcontent.header.sequencenumber)

    return True

  def pass_discovery_ant(self, eventobj: Event):
    previous_address = eventobj.eventcontent.header.interfaceid.split("-")[0]
    messagefrom = eventobj.eventcontent.header.messagefrom.split("-")[1]
    messageto = eventobj.eventcontent.header.messageto.split("-")[1]

    entry = self.get_entry_for_destination(int(messagefrom), int(previous_address))
    
    if (entry is None and int(messagefrom) != self.componentId):
      # make new entry and push it to entries list
      new_entry = ARARoutingEntry(int(messagefrom), int(previous_address))
      new_entry.increasePheromone()
      self.entryTable.append(new_entry)

    # try to push new tuple to visitedAnts and continue if not visited before
    if(self.do_add_to_set(s = self.visitedAnts, added=(eventobj.eventcontent.header.sequencenumber, int(previous_address)))):
      if (int(messageto) == self.componentId):
        if (eventobj.eventcontent.header.messagetype == ARAEventTypes.FANT):
          backward_ant_msg = self.make_ant_packet(
            source=self.componentId,
            destination= int(messagefrom),
            msg_type = ARAEventTypes.BANT)
          self.send_to_neighbors(backward_ant_msg)
        else:
          # means that bant is acquired at the right place, hence find the first message and send it with ARA
          cached_event = self.find_cached_event(eventobj)
          if cached_event is not None: 
            # deep copy the element since we are going to delete it
            cp_cached_event = self.copy_event(cached_event)
            self.msgCache.remove(cached_event)
            self.ARA(cp_cached_event) 
      else:
        # send to all neightbors except previous address
        self.send_to_neighbors(eventobj.eventcontent, previous_address)
    else:
      # ignore the packet
      return

  def pass_loop_packet(self, eventobj: Event):
    previous_sender = int(eventobj.eventcontent.header.interfaceid.split("-")[0])
    message_header = GenericMessageHeader(
      messagetype = ARAEventTypes.DUPLICATE_ERROR,
      messagefrom = eventobj.eventcontent.header.messageto,
      messageto = "RoutingARAComponent-"+str(self.componentId),
      nexthop = previous_sender,
      sequencenumber = uuid4()) # unique sequence number to identify ants
    payload = eventobj # send previous event object in payload to continue searching
    message = GenericMessage(message_header, payload)
    self.send_to_one_neighbor(message, previous_sender)

  def deactivate_loop_route(self, eventobj: Event):
    messageto = eventobj.eventcontent.header.messageto.split("-")[1]
    messagefrom = eventobj.eventcontent.header.messagefrom.split("-")[1]
    target = eventobj.eventcontent.header.interfaceid.split("-")[1]
    previous_msg = eventobj.eventcontent.payload # previous msg is send back in the payload

    if (int(target) == self.componentId):
      # delete the looping route
      for entry in self.entryTable:
        if (entry.destination == int(messagefrom) 
            and 
            entry.nextHopAddress == int(messageto)):
          self.entryTable.remove(entry)

      # handle to previous packet but change its id so fresh start
      new_msg_header = GenericMessageHeader(
        messagetype = previous_msg.eventcontent.header.messagetype,
        messagefrom = previous_msg.eventcontent.header.messagefrom,
        messageto = previous_msg.eventcontent.header.messageto,
        sequencenumber = uuid4())
      payload = ""
      msg = GenericMessage(new_msg_header, payload) 
      self.ARA(Event(self, EventTypes.MFRT, msg))

    else:
      print("ERROR, received DUPLICATE_ERROR was not addressed to me: ", self.componentId)
    
  def do_add_to_set(self, s: Set, added: Tuple) -> bool:
    # checks if adding operation is successfull to set
    l = len(s)
    s.add(added)
    return len(s) != l


  def find_destination_entries(self, destination_adress) -> List[ARARoutingEntry]:
    entries: List[ARARoutingEntry] = []
    for entry in self.entryTable:
      if (entry.destination == destination_adress):
        entries.append(entry)
    return entries

  def find_next_hop(self, entries: List[ARARoutingEntry]) -> ARARoutingEntry:
    total_pheromone = 0.0
    for entry in entries:
      total_pheromone = total_pheromone + entry.pheromone
    
    randomVar = (rand.randint(0, ARAConfiguration.RAND_MAX) / ARAConfiguration.RAND_MAX) * total_pheromone 

    choosenHop = -1
    while (randomVar >= 0.0):
      choosenHop = choosenHop + 1
      if (len(entries) == choosenHop):
        return entries[-1]
      randomVar = randomVar - entries[choosenHop].pheromone

    return entries[choosenHop] 

  def make_ant_packet(self, source, destination, msg_type: ARAEventTypes) -> GenericMessage:
    message_header = GenericMessageHeader(
      messagetype = msg_type,
      messagefrom = "RoutingARAComponent-"+str(source),
      messageto = "RoutingARAComponent-"+str(destination),
      nexthop = 0, # total hop count as header
      sequencenumber = uuid4()) # unique sequence number to identify ants
    payload = "" # empty payload for ants
    message = GenericMessage(message_header, payload)
    return message

  def get_entry_for_destination(self, destination, hop_adress) -> ARARoutingEntry:
    for entry in self.entryTable:
      if (entry.destination == destination and entry.nextHopAddress == hop_adress):
        return entry
    return None

  def send_to_one_neighbor(self, packet: GenericMessage, neighbor):
    if (neighbor not in self.neighbors):
      print("ERROR, neighbor ", neighbor, " is not a neighbor of ", self.componentId)
    else:
      new_packet = self.create_new_packet_with_interface(packet, self.componentId, neighbor)    

      self.send_down(Event(self, EventTypes.MFRT, new_packet))

  def send_to_neighbors(self, packet: GenericMessage, exceptions=[]):
    for n in self.neighbors:
      if (len(exceptions) == 0):
        # create new packet with interface
        new_packet = self.create_new_packet_with_interface(packet, self.componentId, n)
        self.send_down(Event(self, EventTypes.MFRT, new_packet))

      else:
        for e in exceptions:
          if (n != int(e)):
            # set interface id for channels
            new_packet = self.create_new_packet_with_interface(packet, self.componentId, n)
            self.send_down(Event(self, EventTypes.MFRT, new_packet))

  def create_new_packet_with_interface(self, packet: GenericMessage, from_node, to_node) -> GenericMessage:
    message_header = GenericMessageHeader(
      messagetype=packet.header.messagetype,
      messagefrom=packet.header.messagefrom,
      messageto=packet.header.messageto,
      nexthop=to_node,
      interfaceid=str(from_node)+"-"+str(to_node), 
      sequencenumber=packet.header.sequencenumber)
    return GenericMessage(message_header, packet.payload)

  def find_cached_event(self, eventobj: Event) -> Event:
    messageto = eventobj.eventcontent.header.messageto.split("-")[1]
    messagefrom = eventobj.eventcontent.header.messagefrom.split("-")[1]

    # reverse the addresses since this func is called fro BANT event
    for e in self.msgCache:
      header = e.eventcontent.header
      if (header.messageto.split("-")[1] == messagefrom
          and
          header.messagefrom.split("-")[1] == messageto):
        return e
    return None

  def copy_event(self, eventobj: Event) -> Event:
    new_header = GenericMessageHeader(
      messagetype=eventobj.eventcontent.header.messagetype,
      messagefrom=eventobj.eventcontent.header.messagefrom,
      messageto=eventobj.eventcontent.header.messageto,
      nexthop=eventobj.eventcontent.header.nexthop,
      interfaceid=eventobj.eventcontent.header.interfaceid,
      sequencenumber=eventobj.eventcontent.header.sequencenumber
    )
    new_payload = eventobj.eventcontent.payload
    new_msg = GenericMessage(new_header, new_payload)
    new_event = Event(eventobj.eventsource, eventobj.event, new_msg, eventobj.fromchannel, eventobj.eventid)
    return new_event

  def make_interface_id(self, from_node, to_node):
    if int(self.from_node) > int(to_node):
        interfaceid = str(to_node)+"-"+str(from_node)
        return interfaceid
    else:
        interfaceid=str(from_node)+"-"+str(to_node)
        return interfaceid