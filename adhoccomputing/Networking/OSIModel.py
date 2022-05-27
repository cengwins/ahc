from ..Generics import *
from ..GenericModel import *
from .ApplicationLayer.GenericApplicationLayer import *
from .LinkLayer.GenericLinkLayer import *
from .NetworkLayer.GenericNetworkLayer import *
from .TransportLayer.GenericTransportLayer import *
from .LogicalChannels.GenericChannel import GenericChannel

class AHCChannelError(Exception):
  pass

class AdHocNode(GenericModel):

  def on_init(self, eventobj: Event):
    logger.debug(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)

    self.appllayer = GenericApplicationLayer("ApplicationLayer", self.componentinstancenumber)
    self.netlayer = GenericNetworkLayer("NetworkLayer", self.componentinstancenumber)
    self.linklayer = GenericLinkLayer("LinkLayer", self.componentinstancenumber)
    self.transportlayer = GenericTransportLayer("TransportLayer", self.componentinstancenumber)

    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)
    self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)

    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.transportlayer)
    self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    self.components.append(self.appllayer)
    self.components.append(self.netlayer)
    self.components.append(self.linklayer)
    self.components.append(self.transportlayer)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)


  def connect_to_layer(self, down, up, newLayer):
    newLayer.connect_me_to_component(ConnectorTypes.DOWN, down)
    newLayer.connect_me_to_component(ConnectorTypes.UP, up)
    down.connect_me_to_component(ConnectorTypes.UP, newLayer)
    up.connect_me_to_component(ConnectorTypes.DOWN, newLayer)

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
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    elif(indx == 3): # Transport Layer
        self.transportlayer = new(args)
        self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        self.transportlayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.transportlayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)
    elif(indx == 4): # Application Layer
        self.appllayer = new(args)
        self.transportlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.transportlayer)

    else:
      raise("Index number should be between [0,4]")


