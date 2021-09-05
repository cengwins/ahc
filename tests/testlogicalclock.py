import random
import time

import networkx as nx

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import EventTypes
from Channels.Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

from Clocks.LogicalClocks import VectorClock


class ApplicationLayerComponent(ComponentModel):

  def on_init(self, eventobj: Event):
    #print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    if self.componentinstancenumber == 0:
      self.send_down(Event(self, EventTypes.MFRT, None))

  def on_message_from_bottom(self, eventobj: Event):
    randdelay = random.randint(0, 2)
    time.sleep(randdelay)
    self.send_down(Event(self, EventTypes.MFRT, None))  

  def __init__(self, componentname, componentinstancenumber): 
    super().__init__(componentname, componentinstancenumber)
 

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    #print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):
    super().__init__(componentname, componentid)

    # SUBCOMPONENTSc
    self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid)
    self.middleware = VectorClock("VectorClock ", componentid)
    self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
    self.linklayer = LinkLayer("LinkLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.middleware)
    self.middleware.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    self.middleware.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.middleware)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
    

def main():
  
  G = nx.random_geometric_graph(3, 1)
  topo = Topology()
  topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)

  
  topo.start()
  time.sleep(20)


if __name__ == "__main__":
  main()