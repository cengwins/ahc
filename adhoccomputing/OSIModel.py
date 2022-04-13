# from Channels import P2PFIFOPerfectChannel
from definitions import *
from generics import *
from GenericModel import *
from GenericApplicationLayer import *
from GenericLinkLayer import *
from GenericNetworkLayer import *
from GenericTransportLayer import *
from GenericChannel import P2PFIFOPerfectChannel, GenericChannel

class AHCChannelError(Exception):
  pass

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

  def connect_me_to_channel(self, name, channel: GenericChannel):
    try:
        self.connectors[name] = channel
    except AttributeError:
        # self.connectors = ConnectorList()
        self.connectors[name] = channel
    connectornameforchannel = self.componentname + str(self.componentinstancenumber)
      
    channel.connect_me_to_component(connectornameforchannel, self)

  def replace_component(self, new:GenericModel, indx, args):
    if(indx == 0) :        
      self.physicallayer:GenericModel = new(args) 
      self.physicallayer.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
      self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self.physicallayer)
    elif(indx ==1) :
        self.linklayer = new(args)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        if self.physicallayer:
          self.physicallayer.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
          self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self.physicallayer)
    elif(indx == 2): # Network Layer
        self.netlayer = new(args)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.transportlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_channel(ConnectorTypes.UP, self.netlayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    elif(indx == 3): # Transport Layer
        self.transportlayer = new(args)
        self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        self.netlayer.connect_me_to_channel(ConnectorTypes.UP, self.transportlayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)
    elif(indx == 4): # Application Layer
        self.appllayer = new(args)
        self.transportlayer.connect_me_to_channel(ConnectorTypes.UP, self.appllayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)

    else: 
      raise("Index number should be between [0,4]")


