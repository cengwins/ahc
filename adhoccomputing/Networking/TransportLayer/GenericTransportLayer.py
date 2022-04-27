from enum import Enum

from ...Generics import *
from ...GenericModel import GenericModel

class TransportLayerMessages(Enum):
  TRANSPORT_MSG = "TRANSPORT_MSG"

class GenericTransportLayer(GenericModel):

  def on_message_from_top(self, eventobj: Event):
    abovehdr = eventobj.eventcontent.header
    hdr = None
    if abovehdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:
      hdr = GenericMessageHeader(TransportLayerMessages.TRANSPORT_MSG, self.componentinstancenumber,
                                   MessageDestinationIdentifiers.LINKLAYERBROADCAST,nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)
    else:
      #if we do not broadcast, use nexthop to determine interfaceid and set hdr.interfaceid
      myinterfaceid = str(self.componentinstancenumber) + "-" + str(abovehdr.nexthop)
      hdr = GenericMessageHeader(TransportLayerMessages.TRANSPORT_MSG, self.componentinstancenumber,
                                   abovehdr.messageto, nexthop=abovehdr.nexthop, interfaceid=myinterfaceid)


    payload = eventobj.eventcontent
    msg = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, msg))

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.LINKLAYERBROADCAST:
      self.send_up(Event(self, EventTypes.MFRB, payload,
                         eventobj.fromchannel))  # doing decapsulation by just sending the payload
    else:
      pass
