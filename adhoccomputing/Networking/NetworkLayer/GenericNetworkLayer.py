from enum import Enum

from ...Generics import *
from ...GenericModel import *

# define your own message types
class NetworkLayerMessageTypes(Enum):
  NETMSG = "NETMSG"

# define your own message header structure
class NetworkLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class NetworkLayerMessagePayload(GenericMessagePayload):
  pass

class GenericNetworkLayer(GenericModel):

  def __init__(self, componentname, componentinstancenumber, fw_table = {}, context=None, configurationparameters=None, num_worker_threads=1):
    self.fw_table = fw_table
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads)

  def on_message_from_top(self, eventobj: Event):
    # Encapsulate the SDU in network layer PDU
    applmsg = eventobj.eventcontent
    destination = applmsg.header.messageto
    nexthop = self.get_next_hop(self.componentinstancenumber, destination)
    # print(self.fw_table)
    if nexthop != float('inf'):
      # print(f"{self.componentinstancenumber} will SEND a message to {destination} over {nexthop}")
      hdr = NetworkLayerMessageHeader(NetworkLayerMessageTypes.NETMSG, self.componentinstancenumber, destination, nexthop)
      payload = eventobj.eventcontent
      msg = GenericMessage(hdr, payload)
      self.send_down(Event(self, EventTypes.MFRT, msg))
    else:
      pass
      # print(f"NO PATH: {self.componentinstancenumber} will NOTSEND a message to {destination} over {nexthop}")

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload

    if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:  # Add if broadcast....
      self.send_up(Event(self, EventTypes.MFRB, payload))
      # print(f"I received a message to {hdr.messageto} and I am {self.componentinstancenumber}")
    else:
      destination = hdr.messageto
      nexthop = self.get_next_hop(self.componentinstancenumber, destination)
      if nexthop != float('inf'):
        newhdr = NetworkLayerMessageHeader(NetworkLayerMessageTypes.NETMSG, self.componentinstancenumber, destination,
                                           nexthop)
        newpayload = eventobj.eventcontent.payload
        msg = GenericMessage(newhdr, newpayload)
        self.send_down(Event(self, EventTypes.MFRT, msg))
        # print(f"{self.componentinstancenumber} will FORWARD a message to {destination} over {nexthop}")
      else:
        pass
        # print(f"NO PATH {self.componentinstancenumber} will NOT FORWARD a message to {destination} over {nexthop}")

  def get_next_hop(self, fromId, toId):
    try:
      retval = self.fw_table[fromId][toId]
      return retval[1]
    except KeyError:
      return inf
    except IndexError:
      return fromId

