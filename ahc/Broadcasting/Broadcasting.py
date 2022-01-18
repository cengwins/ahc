import random
import time
from enum import Enum

from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes

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

class ControlledFlooding(ComponentModel):
  def on_init(self, eventobj: Event):
    self.uniquebroadcastidentifier = 1
    self.broadcastdb = []
    if self.componentinstancenumber == 0  :
      self.send_self(Event(self, EventTypes.MFRT, None))

  def senddownbroadcast(self, eventobj: Event, whosends, sequencenumber):
    applmsg = eventobj.eventcontent
    destination = MessageDestinationIdentifiers.NETWORKLAYERBROADCAST
    nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
    print(f"{self.componentinstancenumber} will SEND a message to {destination} over {nexthop}")
    hdr = BroadcastingMessageHeader(BroadcastingMessageTypes.SIMPLEFLOOD, whosends, destination,
                                    nexthop, sequencenumber)
    payload = applmsg
    broadcastmessage = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))
    self.broadcastdb.append(broadcastmessage.uniqueid)

  def update_topology(self):
    Topology().nodecolors[self.componentinstancenumber] = 'r'
    Topology().plot()

  def on_broadcast(self, eventobj: Event):
    self.update_topology()
    self.uniquebroadcastidentifier = self.uniquebroadcastidentifier + 1
    self.senddownbroadcast(eventobj, self.componentinstancenumber, self.uniquebroadcastidentifier)
        
  def on_message_from_top(self, eventobj: Event):
    self.update_topology()
    evt = Event(self, BroadcastingEventTypes.BROADCAST, eventobj.eventcontent)
    self.send_self(evt)

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    if hdr.messagetype == BroadcastingMessageTypes.SIMPLEFLOOD:
      if hdr.messageto == self.componentinstancenumber or hdr.messageto == MessageDestinationIdentifiers.NETWORKLAYERBROADCAST:  # Add if broadcast....
        if msg.uniqueid in self.broadcastdb:
          pass  # we have already handled this flooded message
        else:
          # Send to higher layers
          self.update_topology()
          self.send_up(Event(self, EventTypes.MFRB, payload))
          # Also continue flooding once
          time.sleep(random.randint(1, 3))
          self.senddownbroadcast(eventobj, eventobj.eventcontent.header.messagefrom,
                                 eventobj.eventcontent.header.sequencenumber)

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[BroadcastingEventTypes.BROADCAST] = self.on_broadcast
    # add events here
