from random import choice
import time
from enum import Enum
from typing import Any, List
import uuid

from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes

# define your own message types
class WaveMessageTypes(Enum):
  FORWARD = "@tarrys/forward"
  START = "@tarrys/start"

# define your own message header structure
class WaveMessageHeader(GenericMessageHeader):
  def __init__(self, *args, token, **kwargs):
    super().__init__(*args, **kwargs)
    self.token = token

# define your own message payload structure
class WaveMessagePayload(GenericMessagePayload):
  pass

class TarryNeighbor:
  def __init__(self, id, invoked):
    self.id = id
    self.invoked = invoked

class TarrysTraverse(ComponentModel):
  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.token_neighbor_mapping = {}
    self.token_parent_mapping = {}

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    message_source = hdr.messagefrom

    payload:List[Any] = msg.payload.messagepayload

    if hdr.messagetype == WaveMessageTypes.FORWARD or hdr.messagetype == WaveMessageTypes.START:
      token = hdr.token
      if hdr.messagetype == WaveMessageTypes.START:
        self.token_parent_mapping[token] = -1
  
      parent_for_token = self.token_parent_mapping.get(token, None)
      if parent_for_token == None:
        self.token_parent_mapping[token] = message_source
        parent_for_token = message_source

      message = None
      next_target = None
      """
        Tarry's algorithm has 2 rules.
        1 - A process never forwards the token through the same channel twice.
        2 - A process only forwards the token to its parent when there is no other option.
      """
      uninvoked_neighbors = [n for n in self.get_neighbor_mapping_for_token(token) if n.invoked == False and n.id != parent_for_token]
      if len(uninvoked_neighbors) > 0: # If true, send to the available neighbor
        neigh = choice(uninvoked_neighbors)
        # neigh = uninvoked_neighbors[0]
        neigh.invoked = True
        next_target = neigh.id
      else: # Else, send the token back to the parent
        if parent_for_token == -1: # If I am the initiator, traversing is completed
          print("->".join(payload))
          print("TRAVERSING IS COMPLETED IN " + str(len(payload)) + " hops")
          print(f"Graph had {Topology().G.number_of_edges()} edges")
          print(len(set(payload)))
          return
        else:
          next_target = parent_for_token
      payload.append(str(self.componentinstancenumber))
      message = self.prepare_message(WaveMessageTypes.FORWARD, next_target, token, payload)
      self.send_down(Event(self, EventTypes.MFRT, message))

  def start_traverse(self):
    token = self.create_token()
    self.send_self(Event(self, EventTypes.MFRB, self.prepare_message(WaveMessageTypes.START, self.componentinstancenumber, token, [])))

  def create_token(self):
    return str(uuid.uuid4())

  def prepare_neighbor_map(self):
    neighbor_list = Topology().get_neighbors(self.componentinstancenumber)
    # return [{"neighbor": n, "invoked": False} for n in neighbor_list]
    return [TarryNeighbor(n, False) for n in neighbor_list]
  
  def get_neighbor_mapping_for_token(self, token: str) -> List[TarryNeighbor]:
    mapping = self.token_neighbor_mapping.get(token)
    if mapping == None:
      mapping = self.prepare_neighbor_map()
      self.token_neighbor_mapping[token] = mapping
    return mapping

  def prepare_message(self, message_type: WaveMessageTypes, neighbor: int, token: str, payload:str = None ) -> GenericMessage:
    header = WaveMessageHeader(message_type, self.componentinstancenumber, neighbor, neighbor, token=token)
    payload = WaveMessagePayload(payload)
    return GenericMessage(header, payload)