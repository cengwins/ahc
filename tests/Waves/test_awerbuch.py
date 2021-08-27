
__author__ = "One solo developer"
__authors__ = ["Mahmoud Alasmar"]
__contact__ = "mahmoud.asmar@metu.edu.tr"
__date__ = "2021/05/26"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"



import matplotlib.pyplot as plt
import networkx as nx
from Ahc import Topology
from Ahc import ComponentModel, Event, ConnectorTypes, ComponentRegistry
from Ahc import EventTypes
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Waves.AwerbuchDFS import WaveAwerbuchComponent


number_mesg = 0
topo = Topology()
registry = ComponentRegistry()


class AdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
      print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
      self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
      self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
      # SUBCOMPONENTS
      self.appllayer = WaveAwerbuchComponent("ApplicationLayer", componentid)
      self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
      self.linklayer = LinkLayer("LinkLayer", componentid)

      # CONNECTIONS AMONG SUBCOMPONENTS
      self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
      self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

      # Connect the bottom component to the composite component....
      self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
      self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

      super().__init__(componentname, componentid)




def main():
  """
  G = nx.Graph()
  for i in range(5):
    G.add_node(i)

  G.add_edge(0, 1)
  G.add_edge(0, 3)
  G.add_edge(0, 4)
  G.add_edge(1, 2)
  G.add_edge(1, 3)
  G.add_edge(1, 4)
  G.add_edge(2, 1)
  G.add_edge(2, 4)
  G.add_edge(2, 3)
  G.add_edge(3, 1)
  G.add_edge(3, 0)
  G.add_edge(3, 2)
  """
  G = nx.random_geometric_graph(50, 0.5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()

  print("Starting Awerbuch test")
  # topo is defined as a global variable
  topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)
  topo.start()


  plt.show()  # while (True): pass

if __name__ == "__main__":
  main()