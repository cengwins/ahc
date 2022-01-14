from enum import Enum

from ahc.Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, \
  GenericMessage, EventTypes
import threading

# define your own message types
class LinkLayerMessageTypes(Enum):
  LINKMSG = "LINKMSG"

# define your own message header structure
class LinkLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class LinkLayerMessagePayload(GenericMessagePayload):
  pass

class AODVLinkLayerComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    self.lock = threading.Lock()
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On MSFRT LinkLayer {self.componentname}.{self.componentinstancenumber}")
    abovehdr = eventobj.eventcontent.header
    if abovehdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST: #Never goes inside I've implemented else statement
      #print("It broadcasts")
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
    self.lock.release()

  def on_message_from_bottom(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On MSFRB LinkLayer {self.componentname}.{self.componentinstancenumber}")
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.LINKLAYERBROADCAST:
      self.send_up(Event(self, EventTypes.MFRB, payload,
                         eventobj.fromchannel)) 
    else:
      #      print(f"I am {self.componentinstancenumber} and dropping the {hdr.messagetype} message to {hdr.messageto}")
      # Physical layer is a broadcast medium, and hence will accept all messages. The link layer will drop those messages that are not for me
      pass
    self.lock.release()

#  def __init__(self, componentname, componentinstancenumber):
#   super().__init__(componentname, componentinstancenumber)
#   If you have to extend the model add events here
