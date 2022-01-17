from enum import Enum

from ahc.Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, \
  GenericMessage, EventTypes

# define your own message types
class LinkLayerMessageTypes(Enum):
  LINKMSG = "LINKMSG"

# define your own message header structure
class LinkLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class LinkLayerMessagePayload(GenericMessagePayload):
  pass

class LinkLayer(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def on_message_from_top(self, eventobj: Event):
    abovehdr = eventobj.eventcontent.header
    if abovehdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:
      hdr = LinkLayerMessageHeader(LinkLayerMessageTypes.LINKMSG, self.componentinstancenumber,
                                   MessageDestinationIdentifiers.LINKLAYERBROADCAST,nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)
    else:
      #if we do not broadcast, use nexthop to determine interfaceid and set hdr.interfaceid
      myinterfaceid = str(self.componentinstancenumber) + "-" + str(abovehdr.nexthop)
      hdr = LinkLayerMessageHeader(LinkLayerMessageTypes.LINKMSG, self.componentinstancenumber,
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
      #      print(f"I am {self.componentinstancenumber} and dropping the {hdr.messagetype} message to {hdr.messageto}")
      # Physical layer is a broadcast medium, and hence will accept all messages. The link layer will drop those messages that are not for me
      pass

#  def __init__(self, componentname, componentinstancenumber):
#   super().__init__(componentname, componentinstancenumber)
#   If you have to extend the model add events here
