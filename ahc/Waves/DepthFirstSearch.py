from random import choice
import time
from enum import Enum
from typing import Any, Dict, List
import uuid

from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes

# define your own message types
class DfsMessageTypes(Enum):
  FORWARD = "@tarrys/forward"
  START = "@tarrys/start"

# define your own message header structure
class DfsMessageHeader(GenericMessageHeader):
  def __init__(self, *args, token, **kwargs):
    super().__init__(*args, **kwargs)
    self.token = token

# define your own message payload structure
class DfsMessagePayload(GenericMessagePayload):
  pass

class DfsNeighbor:
  def __init__(self, id, invoked):
    self.id = id
    self.invoked = invoked

class DfsTraverse(ComponentModel):
  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.token_neighbor_mapping = {}
    self.token_parent_mapping = {}

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    message_source = hdr.messagefrom

    payload:List[Any] = msg.payload.messagepayload

    if hdr.messagetype == DfsMessageTypes.FORWARD or hdr.messagetype == DfsMessageTypes.START:
      token = hdr.token
      if hdr.messagetype == DfsMessageTypes.START:
        self.token_parent_mapping[token] = -1
  
      parent_for_token = self.token_parent_mapping.get(token, None)
      if parent_for_token == None:
        self.token_parent_mapping[token] = message_source
        parent_for_token = message_source

      message = None
      next_target = None
      """
        DFS's algorithm has 3 rules.
        1 - A process never forwards the token through the same channel twice.
        2 - A process only forwards the token to its parent when there is no other option.
        3 - When a process receives the token, it immediately sends it back through the same 
            channel if this is allowed by rules 1 and 2.
      """
      uninvoked_neighbors = [n for n in self.get_neighbor_mapping_for_token(token) if n.invoked == False and n.id != parent_for_token and n.id != message_source]
      # Send message back if possible
      if message_source in [n.id for n in self.get_neighbor_mapping_for_token(token) if n.invoked == False] and message_source != parent_for_token:
          neigh = [n for n in self.get_neighbor_mapping_for_token(token) if n.invoked == False and n.id == message_source][0]
          neigh.invoked = True
          next_target = message_source
      elif len(uninvoked_neighbors) > 0: # If true, send to the available neighbor
        neigh = choice(uninvoked_neighbors)
        neigh.invoked = True
        next_target = neigh.id
      else: # Else, send the token back to the parent
        if parent_for_token == -1: # If I am the initiator, traversing is completed
          print(payload)
          print("->".join(payload))
          print("TRAVERSING IS COMPLETED IN " + str(len(payload)) + " hops")
          print(f"Graph had {Topology().G.number_of_edges()} edges")
          print(len(set(payload)))
          return
        else:
          next_target = parent_for_token

      payload.append(str(self.componentinstancenumber))
      message = self.prepare_message(DfsMessageTypes.FORWARD, next_target, token, payload)
      self.send_down(Event(self, EventTypes.MFRT, message))

  def start_traverse(self):
    token = self.create_token()
    self.send_self(Event(self, EventTypes.MFRB, self.prepare_message(DfsMessageTypes.START, self.componentinstancenumber, token, [])))

  def create_token(self):
    return str(uuid.uuid4())

  def prepare_neighbor_map(self):
    neighbor_list = Topology().get_neighbors(self.componentinstancenumber)
    return [DfsNeighbor(n, False) for n in neighbor_list]
  
  def get_neighbor_mapping_for_token(self, token: str) -> List[DfsNeighbor]:
    mapping = self.token_neighbor_mapping.get(token)
    if mapping == None:
      mapping = self.prepare_neighbor_map()
      self.token_neighbor_mapping[token] = mapping
    return mapping

  def prepare_message(self, message_type: DfsMessageTypes, neighbor: int, token: str, payload:Any = None) -> GenericMessage:
    header = DfsMessageHeader(message_type, self.componentinstancenumber, neighbor, neighbor, token=token)
    payload = DfsMessagePayload(payload)
    return GenericMessage(header, payload)