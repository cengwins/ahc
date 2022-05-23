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

class GenericChannel(GenericModel):

  def on_init(self, eventobj: Event):
    pass

  # Overwrite onSendToChannel if you want to do something in the first pipeline stage
  def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline
    myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH,
                    eventobj.eventcontent, eventid=eventobj.eventid)
    #self.channelqueue.put_nowait(myevent)
    self.channelqueue.trigger_event(myevent)

  # Overwrite onProcessInChannel if you want to do something in interim pipeline stage
  def on_process_in_channel(self, eventobj: Event):
    # Add delay, drop, change order whatever....
    # Finally put the message in outputqueue with event deliver
    # Preserve the event id through the pipeline
    myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR, eventobj.eventcontent, eventid=eventobj.eventid)
    #print("on_process_in_channel", myevent.eventsource)

    #self.outputqueue.put_nowait(myevent)
    self.outputqueue.trigger_event(myevent)

  # Overwrite onDeliverToComponent if you want to do something in the last pipeline stage
  # onDeliver will deliver the message from the channel to the receiver component using messagefromchannel event
  def on_deliver_to_component(self, eventobj: Event):
    callername = eventobj.eventsource.componentinstancenumber
    #print("on_deliver_to_component", self.componentname)
    for item in self.connectors:
      #print("item", item)
      callees = self.connectors[item]
      for callee in callees:
        calleename = callee.componentinstancenumber
        #print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
        if calleename == callername:
          #print("Dont send self")
          pass
        else:
          # Preserve the event id through the pipeline
          myevent = Event(eventobj.eventsource, EventTypes.MFRB,
                          eventobj.eventcontent, self.componentinstancenumber,
                          eventid=eventobj.eventid)
          callee.trigger_event(myevent)
          #print("I am delivering to ",callee )

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    #self.outputqueue = queue.Queue()
    #self.channelqueue = queue.Queue()
    self.outputqueue = self.manager.Queue()
    self.channelqueue = self.manager.Queue()
    self.eventhandlers[ChannelEventTypes.INCH] = self.on_process_in_channel
    self.eventhandlers[ChannelEventTypes.DLVR] = self.on_deliver_to_component

    self.t = [None]*self.num_worker_threads
    self.t1 = [None]*self.num_worker_threads
    
    for i in range(self.num_worker_threads):
      # note that the input queue is handled by the super class...
      self.t[i] = Thread(target=self.queue_handler, args=[self.channelqueue])
      self.t1[i]  = Thread(target=self.queue_handler, args=[self.outputqueue])
      self.t[i].daemon = True
      self.t1[i].daemon = True
      self.t[i].start()
      self.t1[i].start()


class P2PFIFOPerfectChannel(GenericChannel):

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)


  # Overwrite onSendToChannel
  # Channels are broadcast, that is why we have to check channel id's using hdr.interfaceid for P2P
  def on_message_from_top(self, eventobj: Event):
    # if channelid != hdr.interfaceif then drop (should not be on this channel)
    hdr = eventobj.eventcontent.header
    if hdr.nexthop != MessageDestinationIdentifiers.LINKLAYERBROADCAST:
      if set(hdr.interfaceid.split("-")) == set(self.componentinstancenumber.split("-")):
        #print(f"Will forward message since {hdr.interfaceid} and {self.componentinstancenumber}")
        myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH, eventobj.eventcontent)
        #self.channelqueue.put_nowait(myevent)
        self.channelqueue.trigger_event(myevent)
      else:
        # print(f"Will drop message since {hdr.interfaceid} and {self.componentinstancenumber}")
        pass

  def on_deliver_to_component(self, eventobj: Event):
    msg = eventobj.eventcontent
    caller_id = eventobj.eventsource.componentinstancenumber
    for connector in self.connectors:
      callee = self.connectors[connector]
      for caller in callee:
        callee_id = caller.componentinstancenumber
        # return
        #print(f"I am connected to {callee}. Will check if I have to distribute it to {callee_id}")
        if callee_id == caller_id:
          pass
        else:
          myevent = Event(eventobj.eventsource, EventTypes.MFRB, eventobj.eventcontent, self.componentinstancenumber)
          caller.trigger_event(myevent)

  def connect_me_to_component(self, name, component):
    try:
      self.connectors[name] = component
      if len(self.connectors) > 2:
        raise AHCChannelError("More than two nodes cannot connect to a P2PFIFOChannel")
    except AttributeError:
      # self.connectors = ConnectorList()
      self.connectors[name] = component
    # except AHCChannelError as e:
    #    print( f"{e}" )




# class BasicLossyChannel(Channel):
#   def __init__(self, componentname, componentinstancenum, loss_percentage=0):
#     super().__init__(componentname, componentinstancenum,)
#     self.loss_percentage = loss_percentage
#   # Overwrite onDeliverToComponent if you want to do something in the last pipeline stage
#   # onDeliver will deliver the message from the channel to the receiver component using messagefromchannel event
#   def on_deliver_to_component(self, eventobj: Event):
#     callername = eventobj.eventsource.componentinstancenumber
#     for item in self.connectors:
#       callees = self.connectors[item]
#       for callee in callees:
#         calleename = callee.componentinstancenumber
#         # print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
#         if calleename == callername:
#           pass
#         else:
#           randomnum = random.uniform(0, 1)
#           # print("random number here is " , randomnum, " for ", self.componentinstancenumber)
#           if randomnum >= self.loss_percentage:
#             myevent = Event(eventobj.eventsource, EventTypes.MFRB, eventobj.eventcontent, self.componentinstancenumber)
#             callee.trigger_event(myevent)


# class AHCChannelError(Exception):
#   pass

# class P2PFIFOFairLossChannel(P2PFIFOPerfectChannel):
#   prob = 1
#   duplicationprobability = 0
#   # Overwrite onSendToChannel
#   # Channels are broadcast, that is why we have to check channel id's using hdr.interfaceid for P2P

#   def on_message_from_top(self, eventobj: Event):
#     # if channelid != hdr.interfaceif then drop (should not be on this channel)
#     hdr = eventobj.eventcontent.header
#     if hdr.nexthop != MessageDestinationIdentifiers.LINKLAYERBROADCAST:
#       if set(hdr.interfaceid.split("-")) == set(self.componentinstancenumber.split("-")):
#         #print(f"Will forward message since {hdr.interfaceid} and {self.componentinstancenumber}")
#         myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH, eventobj.eventcontent)
#         self.channelqueue.put_nowait(myevent)
#       else:
#         #print(f"Will drop message since {hdr.interfaceid} and {self.componentinstancenumber}")
#         pass


#   def on_process_in_channel(self, eventobj: Event):
#     if random.random() < self.prob:
#       myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR, eventobj.eventcontent)
#       self.outputqueue.put_nowait(myevent)
#     if random.random() < self.duplicationprobability:
#       self.channelqueue.put_nowait(eventobj)

#   def setPacketLossProbability(self, prob):
#     self.prob = prob

#   def setAverageNumberOfDuplicates(self, d):
#     if d > 0:
#       self.duplicationprobability = (d - 1) / d
#     else:
#       self.duplicationprobability = 0

class FIFOBroadcastPerfectChannel(GenericChannel):
  pass
