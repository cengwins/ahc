from enum import Enum
import time

from Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes, ConnectorTypes, registry
from Channels import TagToTagFIFOPerfectChannel

class TagMessageTypes(Enum):
  SND = "SENDDISTANCE"

# define your own message header structure
class TagMessageHeader(GenericMessageHeader):
  def __init__(self, messagetype, messagefrom, messageto, initialdistance, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
    self.initialdistance = initialdistance
    super().__init__(messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber)

# define your own message payload structure
class TagMessagePayload(GenericMessagePayload):
  pass

class TagMessage(GenericMessage):
  pass

class TagMessageDestinationIdentifiers(Enum):
  SHAREDISTANCEEXCEPTPARENT = -3

class TagComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def start_initiator(self):
    self.starting_message_timestamp = time.perf_counter()
    self.last_incoming_message_timestamp = self.starting_message_timestamp
    # print("Started")
    self.initial_distance = 0
    self.fill_channels_id_list_except_parent()
    self.send_message_to_down()

  def fill_channels_id_list_except_parent(self):
    self.channels_id_list_except_parent = []
    if ConnectorTypes.DOWN in self.connectors[ConnectorTypes.DOWN][0].connectors:
      for channel in self.connectors[ConnectorTypes.DOWN][0].connectors[ConnectorTypes.DOWN]:
        if self.initial_parent_channel != channel.componentinstancenumber:
          self.channels_id_list_except_parent.append(channel.componentinstancenumber)

  def prepare_outgoing_message(self, messagetype, messagefrom, messageto, initialdistance, interface_id):
    message_header = TagMessageHeader(messagetype, messagefrom, messageto, initialdistance, interfaceid=interface_id)
    message_payload = TagMessagePayload(None)
    message = TagMessage(message_header, message_payload)
    return Event(self, EventTypes.MFRT, message)

  def send_message_to_down(self):
    # Gönderilen mesajlar buraya
    for channel_id in self.channels_id_list_except_parent:
      self.send_down(self.prepare_outgoing_message(TagMessageTypes.SND, self.componentinstancenumber, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT, self.initial_distance, channel_id))

  def on_message_from_bottom(self, eventobj: Event):
    # Alınan mesajlar buraya
    message_header = eventobj.eventcontent.header
    message_type = message_header.messagetype
    message_from = message_header.messagefrom
    message_to = message_header.messageto
    incoming_distance = message_header.initialdistance
    incoming_channel = message_header.interfaceid
    incoming_edge_weight = registry.get_component_by_key(TagToTagFIFOPerfectChannel.__name__, incoming_channel).edgeweight

    if message_type == TagMessageTypes.SND:
      self.last_incoming_message_timestamp = time.perf_counter()
      if incoming_distance + incoming_edge_weight < self.initial_distance:
        self.initial_distance = incoming_distance + incoming_edge_weight
        self.initial_parent = message_from
        self.initial_parent_channel = incoming_channel

        self.fill_channels_id_list_except_parent()
        self.send_message_to_down()

  def __init__(self, componentname, componentinstancenumber):
    self.initial_distance = float('inf')
    self.initial_parent = None
    self.initial_parent_channel = None
    self.last_incoming_message_timestamp = None
    self.channels_id_list_except_parent = []
    super().__init__(componentname, componentinstancenumber)
