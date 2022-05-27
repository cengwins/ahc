from enum import Enum

from ...Generics import *
from ...GenericModel import GenericModel

class LinkLayerMessageTypes(Enum):
  LINKMSG = "LINKMSG"

class GenericLinkLayer(GenericModel):

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)

  def on_message_from_top(self, eventobj: Event):
    logger.info(f"{self.componentname}-{self.componentinstancenumber} RECEIVED FROM TOP {str(eventobj)}")
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
    logger.info(f"{self.componentname}-{self.componentinstancenumber} RECEIVED FROM BOTTOM {str(eventobj)}")
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.LINKLAYERBROADCAST:
      self.send_up(Event(self, EventTypes.MFRB, payload,
                         fromchannel= eventobj.fromchannel))  # doing decapsulation by just sending the payload
    else:
      pass
