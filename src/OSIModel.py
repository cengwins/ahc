# from Channels import P2PFIFOPerfectChannel
from definitions import *
from generics import *
from GenericModel import *
from GenericApplicationLayer import *
from GenericLinkLayer import *
from GenericNetworkLayer import *
from GenericTransportLayer import *

# Testing
import networkx as nx
import matplotlib.pyplot as plt

class ChannelEventTypes(Enum):
  INCH = "processinchannel"
  DLVR = "delivertocomponent"


class AHCChannelError(Exception):
  pass
class Channel(GenericModel):

  def on_init(self, eventobj: Event):
    pass

  # Overwrite onSendToChannel if you want to do something in the first pipeline stage
  def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline
    myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH,
                    eventobj.eventcontent, eventid=eventobj.eventid)
    self.channelqueue.put_nowait(myevent)

  # Overwrite onProcessInChannel if you want to do something in interim pipeline stage
  def on_process_in_channel(self, eventobj: Event):
    # Add delay, drop, change order whatever....
    # Finally put the message in outputqueue with event deliver
    # Preserve the event id through the pipeline
    print("saa")
    myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR,
                    eventobj.eventcontent, eventid=eventobj.eventid)
    self.outputqueue.put_nowait(myevent)

  # Overwrite onDeliverToComponent if you want to do something in the last pipeline stage
  # onDeliver will deliver the message from the channel to the receiver component using messagefromchannel event
  def on_deliver_to_component(self, eventobj: Event):
    print("zaa")
    callername = eventobj.eventsource.componentinstancenumber
    for item in self.connectors:
      callees = self.connectors[item]
      for callee in callees:
        calleename = callee.componentinstancenumber
        # print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
        if calleename == callername:
          pass
        else:
          # Preserve the event id through the pipeline
          myevent = Event(eventobj.eventsource, EventTypes.MFRB,
                          eventobj.eventcontent, self.componentinstancenumber,
                          eventid=eventobj.eventid)
          callee.trigger_event(myevent)

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.outputqueue = queue.Queue()
    self.channelqueue = queue.Queue()
    self.eventhandlers[ChannelEventTypes.INCH] = self.on_process_in_channel
    self.eventhandlers[ChannelEventTypes.DLVR] = self.on_deliver_to_component


class P2PFIFOPerfectChannel(Channel):

  def __init__(self, componentname, componentinstancenumber):
      super().__init__(componentname, componentinstancenumber)
      self.connectors = {}
  # Overwrite onSendToChannel
  # Channels are broadcast, that is why we have to check channel id's using hdr.interfaceid for P2P
  def on_message_from_top(self, eventobj: Event):
    # if channelid != hdr.interfaceif then drop (should not be on this channel)
    hdr = eventobj.eventcontent.header
    if hdr.nexthop != MessageDestinationIdentifiers.LINKLAYERBROADCAST:
      if set(hdr.interfaceid.split("-")) == set(self.componentinstancenumber.split("-")):
        print(f"Will forward message since {hdr.interfaceid} and {self.componentinstancenumber}")
        myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH, eventobj.eventcontent)
        self.channelqueue.put_nowait(myevent)
      else:
        #print(f"Will drop message since {hdr.interfaceid} and {self.componentinstancenumber}")
        pass

  def on_deliver_to_component(self, eventobj: Event):
    msg = eventobj.eventcontent
    callername = eventobj.eventsource.componentinstancenumber
    for item in self.connectors:
      callees = self.connectors[item]
      for callee in callees:
        calleename = callee.componentinstancenumber
        # print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
        if calleename == callername:
          pass
        else:
          myevent = Event(eventobj.eventsource, EventTypes.MFRB, eventobj.eventcontent, self.componentinstancenumber)
          callee.trigger_event(myevent)

  # Overwriting to limit the number of connected components
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


class AdHocNode(GenericModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))


  def __init__(self, componentname, componentid, fw_table):
    super().__init__(componentname, componentid)

    self.appllayer = GenericApplicationLayer("ApplicationLayer", self.componentinstancenumber)
    self.netlayer = GenericNetworkLayer("NetworkLayer", self.componentinstancenumber, fw_table)      
    self.linklayer = GenericLinkLayer("LinkLayer", self.componentinstancenumber) 
    self.transportlayer = GenericTransportLayer("TransportLayer", self.componentinstancenumber) 

    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)
    self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)

    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.transportlayer)
    self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
    
  
  def connect_to_layer(self, down, up, newLayer):
    newLayer.connect_me_to_component(ConnectorTypes.DOWN, down)
    newLayer.connect_me_to_component(ConnectorTypes.UP, up)
    down.connect_me_to_component(ConnectorTypes.UP, newLayer)
    up.connect_me_to_component(ConnectorTypes.DOWN, newLayer)

  def connect_me_to_channel(self, name, channel: Channel):
    try:
        self.connectors[name] = channel
    except AttributeError:
        # self.connectors = ConnectorList()
        self.connectors[name] = channel
    connectornameforchannel = self.componentname + str(self.componentinstancenumber)
      
    channel.connect_me_to_component(connectornameforchannel, self)

  def replace_component(self, new:GenericModel, indx, args):
    match indx:
      case 0: # Physical Layer
        
        self.physicallayer:GenericModel = new(args) 
        self.physicallayer.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self.physicallayer)
      case 1: # Link Layer
        self.linklayer = new(args)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        if self.physicallayer:
          self.physicallayer.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
          self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self.physicallayer)
      case 2: # Network Layer
        self.netlayer = new(args)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.transportlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_channel(ConnectorTypes.UP, self.netlayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
      case 3: # Transport Layer
        self.transportlayer = new(args)
        self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        self.netlayer.connect_me_to_channel(ConnectorTypes.UP, self.transportlayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)
      case 4: # Application Layer
        self.appllayer = new(args)
        self.transportlayer.connect_me_to_channel(ConnectorTypes.UP, self.appllayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)


