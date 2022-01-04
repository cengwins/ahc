from Channels.Channels import P2PFIFOPerfectChanne
from definitions import *
from generics import *
from helpers import *
from src.topology import ComponentModel
from topology import ComponentModel
from Layers.NetworkLayers.AllSeeingEyeNetworkLayer import *
from Layers.LinkLayers.GenericLinkLayer import *
from Layers.ApplicationLayers.GenericApplication import *
class LayerTypes(Enum):
  NET = "network"
  LINK = "link"
  TRANS = "transport"
  APP = "app"
  PHY = "physical"

class LayerOrder:
  order = [
    LayerTypes.APP,
    LayerTypes.TRANS,
    LayerTypes.NET,
    LayerTypes.LINK
  ]

  def custom_layerization(self, order): 
    self.order = order

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, layerOrder: LayerOrder):

    for i in layerOrder.order: 
      match i: 
        case LayerTypes.APP:
          self.appllayer = ApplicationLayerComponent("ApplicationLayer", self.componentinstancenumber)
        case LayerTypes.TRANS:
            pass
        case LayerTypes.NET: 
          self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", self.componentinstancenumber)      
        case LayerTypes.LINK: 
          self.linklayer = LinkLayer("LinkLayer", self.componentinstancenumber) 
          
    # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, self.componentinstancenumber)


    def connect_layers(self, layer, last):
      pass
