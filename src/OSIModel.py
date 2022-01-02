
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
  layerOrder = [
    LayerTypes.APP,
    LayerTypes.TRANS,
    LayerTypes.NET,
    LayerTypes.LINK
  ]

  def custom_layerization(self, layerOrder): 
    self.layerOrder = layerOrder

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, LlayerOrder):

    self.appllayer = ApplicationLayerComponent("ApplicationLayer", self.componentinstancenumber)
    self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", self.componentinstancenumber)
    self.linklayer = LinkLayer("LinkLayer", self.componentinstancenumber)
    # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, componentid)
