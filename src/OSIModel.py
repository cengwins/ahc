from Channels.Channels import P2PFIFOPerfectChanne
from definitions import *
from generics import *
from helpers import *
from src.topology import ComponentModel
from topology import ComponentModel
from GenericApplicationLayer import *
from GenericLinkLayer import *
from GenericNetworkLayer import *
class LayerTypes(Enum):
  NET = "network"
  LINK = "link"
  TRANS = "transport"
  APP = "app"
  PHY = "physical"


class AdHocNode(GenericModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname):

    self.appllayer = ApplicationLayerComponent("ApplicationLayer", self.componentinstancenumber)
    self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", self.componentinstancenumber)      
    self.linklayer = LinkLayer("LinkLayer", self.componentinstancenumber) 
          
    # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, self.componentinstancenumber)
  
  def connect_to_layer(self, down: ComponentModel, up: ComponentModel, newLayer: ComponentModel):
    newLayer.connect_me_to_component(ConnectorTypes.DOWN, down)
    newLayer.connect_me_to_component(ConnectorTypes.UP, up)
    down.connect_me_to_component(ConnectorTypes.UP, newLayer)
    up.connect_me_to_component(ConnectorTypes.DOWN, newLayer)
