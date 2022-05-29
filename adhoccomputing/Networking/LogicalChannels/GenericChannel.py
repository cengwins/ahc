from asyncore import loop
from platform import node
import queue
from audioop import mul
from enum import Enum
from threading import Thread


from ...Generics import *
from ...GenericModel import *

# TODO: Channel failure models: lossy-link, fair-loss, stubborn links, perfect links (WHAT ELSE?), FIFO perfect
# TODO: Logged perfect links (tolerance to crashes), authenticated perfect links
# TODO: Broadcast channels? and their failure models? Collisions?
# TODO: Properties of all models separately: e.g., Fair loss, finite duplication, no fabrication in fair-loss link model
# TODO: Packets: loss, duplication, sequence change, windowing?,
# TODO: Eventually (unbounded time) or bounded time for message delivery?


# # Channels have three events: sendtochannel, processinchannel and delivertocomponent
# # Components tell channels to handle a message by the EventTypes.MFRT event, the component calls senddown with the event EventTypes.MFRT
# # First pipeline stage moves the message to the interim pipeline stage with the "processinchannel" event for further processing, such as  the channel may drop it, delay it, or whatever
# # Channels deliver the message to output queue by the "delivertocomponent" event
# # The output queue then will send the message up to the connected component(s) using the "messagefromchannel" event
# # The components that will use the channel directly, will have to handle "messagefromchannel" event

class ChannelEventTypes(Enum):
  INCH = "processinchannel"
  DLVR = "delivertocomponent"


class AHCChannelError(Exception):
  pass


class ChannelPipe(GenericModel):
  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)

  def on_message_from_peer(self, eventobj: Event):
    self.send_peer(eventobj)


class GenericChannel(GenericModel):

  #SENDERNODE --> CHANNEL --> INGRESS --> INTERIM --> EGRESS -> CHANNEL --> RECEIVERNODE
  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)
    self.ingresspipe = ChannelPipe(self.componentname+"-INGRESS", self.componentinstancenumber,context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)
    self.interimpipe =  ChannelPipe(self.componentname+"-INTERIM", self.componentinstancenumber,context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)
    self.egresspipe =  ChannelPipe(self.componentname+"-EGRESS", self.componentinstancenumber,context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)

    self.connect_me_to_component(ConnectorTypes.PEER, self.ingresspipe)
    self.ingresspipe.connect_me_to_component(ConnectorTypes.PEER, self.interimpipe)
    self.interimpipe.connect_me_to_component(ConnectorTypes.PEER, self.egresspipe)
    self.egresspipe.connect_me_to_component(ConnectorTypes.PEER, self)
    
    self.components.append(self.ingresspipe)
    self.components.append(self.interimpipe)
    self.components.append(self.egresspipe)

  def on_message_from_top(self, eventobj: Event):
    eventobj.event = EventTypes.MFRP
    eventobj.fromchannel = self.componentinstancenumber
    self.send_peer(eventobj)

  def on_message_from_peer(self, eventobj: Event):
    logger.debug(f"{self.componentname}-{self.componentinstancenumber} on_deliver_to_component {self.componentname}")
    myevent = Event(self, EventTypes.MFRB,
                     eventobj.eventcontent, fromchannel=self.componentinstancenumber,
                     eventid=eventobj.eventid, eventsource_componentname=eventobj.eventsource_componentname, eventsource_componentinstancenumber=eventobj.eventsource_componentinstancenumber)
    myevent.eventsource=None
    self.send_up_from_channel(myevent, loopback=False)

class GenericChannelWithLoopback(GenericChannel):

  def on_message_from_peer(self, eventobj: Event):
    logger.debug(f"{self.componentname}-{self.componentinstancenumber} on_deliver_to_component {self.componentname}")
    myevent = Event(self, EventTypes.MFRB,
                     eventobj.eventcontent, fromchannel=self.componentinstancenumber,
                     eventid=eventobj.eventid, eventsource_componentname=eventobj.eventsource_componentname, eventsource_componentinstancenumber=eventobj.eventsource_componentinstancenumber)
    myevent.eventsource=None
    self.send_up_from_channel(myevent, loopback=True)

class FIFOBroadcastPerfectChannel(GenericChannel):
  pass
