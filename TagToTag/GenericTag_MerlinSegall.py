from enum import Enum
import time

from Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes, ConnectorTypes, registry
from Channels import TagToTagFIFOPerfectChannel

class TagMessageTypes(Enum):
  RZS = "ROUNDZEROSENDDISTANCE"
  ORS = "OTHERROUNDSSENDDISTANCE"

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
  SHAREDISTANCETOPARENT = -3
  SHAREDISTANCEEXCEPTPARENT = -4

class TagComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def fill_lists(self):
    self.all_incoming_messages = []
    self.channels_id_list_except_parent = []
    self.temp_channels_id_list = []
    if ConnectorTypes.DOWN in self.connectors[ConnectorTypes.DOWN][0].connectors:
      for channel in self.connectors[ConnectorTypes.DOWN][0].connectors[ConnectorTypes.DOWN]:
        if self.initial_parent_channel != channel.componentinstancenumber:
          self.channels_id_list_except_parent.append(channel.componentinstancenumber)
        self.temp_channels_id_list.append(channel.componentinstancenumber)
    # for channel in self.connectors[ConnectorTypes.DOWN][0].connectors[ConnectorTypes.DOWN]:
    #   for node in channel.connectors:
    #     if self.componentinstancenumber != channel.connectors[node][0].componentinstancenumber:
    #       tosendlist.append(channel.connectors[node][0].componentinstancenumber)

  def prepare_outgoing_message(self, messagetype, messagefrom, messageto, initialdistance, interface_id):
    message_header = TagMessageHeader(messagetype, messagefrom, messageto, initialdistance, interfaceid=interface_id)
    message_payload = TagMessagePayload(None)
    message = TagMessage(message_header, message_payload)
    return Event(self, EventTypes.MFRT, message)

  def start_initiator(self, node_count):
    self.starting_message_timestamp = time.perf_counter()
    # print("Started")
    self.is_initiator = True
    self.initial_distance = 0
    self.round_count = node_count - 1
    self.fill_lists()
    self.send_message_to_down(TagMessageTypes.RZS, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT)

  def send_message_to_down(self, message_type: TagMessageTypes, message_identifier: TagMessageDestinationIdentifiers, parent_channel_id=None):
    # Gönderilen mesajlar buraya
    if message_identifier == TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT:
      for channel_id in self.channels_id_list_except_parent:
        self.send_down(self.prepare_outgoing_message(message_type, self.componentinstancenumber, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT, self.initial_distance, channel_id))
    elif message_identifier == TagMessageDestinationIdentifiers.SHAREDISTANCETOPARENT:
      self.send_down(self.prepare_outgoing_message(message_type, self.componentinstancenumber, TagMessageDestinationIdentifiers.SHAREDISTANCETOPARENT, self.initial_distance, parent_channel_id))

  def on_message_from_bottom(self, eventobj: Event):
    # Alınan mesajlar buraya
    message_header = eventobj.eventcontent.header
    message_type = message_header.messagetype
    message_from = message_header.messagefrom
    message_to = message_header.messageto
    incoming_distance = message_header.initialdistance
    incoming_channel = message_header.interfaceid
    incoming_edge_weight = registry.get_component_by_key(TagToTagFIFOPerfectChannel.__name__, incoming_channel).edgeweight

    if message_type == TagMessageTypes.RZS:
      if self.initial_parent == None and self.is_initiator == False:
        self.initial_parent = message_from
        self.initial_parent_channel = incoming_channel
        self.fill_lists()
        self.temp_channels_id_list.remove(incoming_channel)
        self.send_message_to_down(TagMessageTypes.RZS, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT)
      else:
        self.temp_channels_id_list.remove(incoming_channel)

      if len(self.temp_channels_id_list) == 0:
        self.fill_lists()
        if self.is_initiator == False:
          self.send_message_to_down(TagMessageTypes.RZS, TagMessageDestinationIdentifiers.SHAREDISTANCETOPARENT, self.initial_parent_channel)
        else:
          self.send_message_to_down(TagMessageTypes.ORS, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT)

    elif message_type == TagMessageTypes.ORS:
      if incoming_channel == self.initial_parent_channel and self.is_initiator == False:
        self.temp_channels_id_list.remove(incoming_channel)
        if self.initial_distance == float('inf'):
          self.initial_distance = incoming_distance + incoming_edge_weight
        self.send_message_to_down(TagMessageTypes.ORS, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT)
      else:
        self.temp_channels_id_list.remove(incoming_channel)
        if self.is_initiator == False:
          self.all_incoming_messages.append((incoming_distance + incoming_edge_weight, message_from, incoming_channel))

      if len(self.temp_channels_id_list) == 0:
        self.all_incoming_messages.sort(key = lambda x: x[0])
        if len(self.all_incoming_messages) > 0 and self.all_incoming_messages[0][0] < self.initial_distance:
          self.initial_distance = self.all_incoming_messages[0][0]
          self.initial_parent = self.all_incoming_messages[0][1]
          old_parent_channel = self.initial_parent_channel
          self.initial_parent_channel = self.all_incoming_messages[0][2]
          self.fill_lists()
          self.send_message_to_down(TagMessageTypes.ORS, TagMessageDestinationIdentifiers.SHAREDISTANCETOPARENT, old_parent_channel)
        else:
          self.fill_lists()
          if self.is_initiator == False:
            self.send_message_to_down(TagMessageTypes.ORS, TagMessageDestinationIdentifiers.SHAREDISTANCETOPARENT, self.initial_parent_channel)
          else:
            self.round_count -= 1
            if self.round_count > 0:
              self.send_message_to_down(TagMessageTypes.ORS, TagMessageDestinationIdentifiers.SHAREDISTANCEEXCEPTPARENT)
            else:
              # print("Finished")
              self.ending_message_timestamp = time.perf_counter()

  def __init__(self, componentname, componentinstancenumber):
    self.is_initiator = False
    self.initial_distance = float('inf')
    self.initial_parent = None
    self.initial_parent_channel = None
    self.channels_id_list_except_parent = []
    self.temp_channels_id_list = []
    self.all_incoming_messages = []
    super().__init__(componentname, componentinstancenumber)
