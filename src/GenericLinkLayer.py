from enum import Enum
from generics import *
from topology import ComponentModel
from definitions import *

class LinkLayerMessageTypes(Enum):
  LINKMSG = "LINKMSG"

class LinkLayer(ComponentModel):

  def on_message_from_top(self, eventobj: Event):
    abovehdr = eventobj.eventcontent.header
    if abovehdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:
      hdr = GenericMessageHeader(LinkLayerMessageTypes.LINKMSG, self.componentinstancenumber,
                                   MessageDestinationIdentifiers.LINKLAYERBROADCAST,nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)
    else:
      #if we do not broadcast, use nexthop to determine interfaceid and set hdr.interfaceid
      myinterfaceid = str(self.componentinstancenumber) + "-" + str(abovehdr.nexthop)
      hdr = GenericMessageHeader(LinkLayerMessageTypes.LINKMSG, self.componentinstancenumber,
                                   abovehdr.nexthop, nexthop=abovehdr.nexthop, interfaceid=myinterfaceid)

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
