from enum import Enum
import copy
from ...Generics import *
from ...GenericModel import GenericModel

class BroadcastingEventTypes(Enum):
  BROADCAST = "broadcast"

# define your own message types
class BroadcastingMessageTypes(Enum):
  SIMPLEFLOOD = "SIMPLEFLOOD"

# define your own message header structure
class BroadcastingMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class BroadcastingMessagePayload(GenericMessagePayload):
  pass

class ControlledFlooding(GenericModel):
  def on_init(self, eventobj: Event):
    self.uniquebroadcastidentifier = 1
    self.broadcastdb = []


  def senddownbroadcast(self, eventobj: Event, whosends, sequencenumber):
    applmsg = eventobj.eventcontent
    destination = MessageDestinationIdentifiers.NETWORKLAYERBROADCAST
    nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
    logger.info(f"{self.componentinstancenumber} will SEND a message to {destination} over {nexthop}")
    interfaceid = float('inf')  
    hdr = BroadcastingMessageHeader(BroadcastingMessageTypes.SIMPLEFLOOD, whosends, destination,
                                    nexthop, interfaceid=interfaceid,sequencenumber=sequencenumber)
    payload = applmsg
    broadcastmessage = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))
    self.broadcastdb.append(broadcastmessage.uniqueid)

  def on_broadcast(self, eventobj: Event):
    self.uniquebroadcastidentifier = self.uniquebroadcastidentifier + 1
    self.senddownbroadcast(eventobj, self.componentinstancenumber, self.uniquebroadcastidentifier)

  def on_message_from_top(self, eventobj: Event):
    evt = Event(self, BroadcastingEventTypes.BROADCAST, eventobj.eventcontent)
    self.send_self(evt)

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    logger.info(f"{self.componentname}-{self.componentinstancenumber} RECEIVED {str(eventobj)}")
    if hdr.messagetype == BroadcastingMessageTypes.SIMPLEFLOOD:
      if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:  # Add if broadcast....
        if msg.uniqueid in self.broadcastdb:
          pass  # we have already handled this flooded message
        else:
          # Send to higher layers
          evt: Event = copy.copy(eventobj)
          evt.event = EventTypes.MFRB
          self.send_up(evt)
          # Also continue flooding once
          #time.sleep(random.randint(1, 3))
          event = Event(self, BroadcastingEventTypes.BROADCAST, payload)
          self.senddownbroadcast(event, eventobj.eventcontent.header.messagefrom, eventobj.eventcontent.header.sequencenumber)
          #self.senddownbroadcast(eventobj, eventobj.eventcontent.header.messagefrom,
          #                       eventobj.eventcontent.header.sequencenumber)

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    self.eventhandlers[BroadcastingEventTypes.BROADCAST] = self.on_broadcast
