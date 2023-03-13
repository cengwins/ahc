
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
from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.NetworkLayer.GenericNetworkLayer import GenericNetworkLayer
from adhoccomputing.DistributedAlgorithms.Waves.AwerbuchDFS import WaveAwerbuchComponent
from adhoccomputing.Networking.LogicalChannels.GenericChannel import P2PFIFOPerfectChannel

number_mesg = 0
topo = Topology()


class AdHocNode(GenericModel):

    def on_init(self, eventobj: Event):
      print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
      self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
      self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid, topology=None):
      super().__init__(componentname, componentid, topology=topo)
      self.components = []
      # SUBCOMPONENTS
      self.appllayer = WaveAwerbuchComponent("ApplicationLayer", componentid, topology=topology)
      self.netlayer = GenericNetworkLayer("NetworkLayer", componentid, topology=topology)
      self.linklayer = GenericLinkLayer("LinkLayer", componentid)
      self.components.append(self.appllayer)
      self.components.append(self.netlayer)
      self.components.append(self.linklayer)
      print(self.components)

      # CONNECTIONS AMONG SUBCOMPONENTS
      self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
      self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
      self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

      # Connect the bottom component to the composite component....
      self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
      self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

      




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