import os
import sys
import random

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from Ahc import ComponentRegistry
from Broadcasting.Broadcasting import ControlledFlooding
from PhysicalLayer.Channels import P2PFIFOFairLossChannel
from LinkLayers.GenericLinkLayer import LinkLayer

registry = ComponentRegistry()

class AdHocNode(ComponentModel):
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.broadcastservice = ControlledFlooding("SimpleFlooding", componentid)
    self.linklayer = LinkLayer("LinkLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.broadcastservice.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.broadcastservice)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, componentid)

#    self.eventhandlers[EventTypes.MFRT] = self.onMessageFromTop
#    self.eventhandlers["messagefromchannel"] = self.onMessageFromChannel

def main():
  # G = nx.Graph()
  # G.add_nodes_from([1, 2])
  # G.add_edges_from([(1, 2)])
  # nx.draw(G, with_labels=True, font_weight='bold')
  # plt.draw()
  G = nx.random_geometric_graph(19, 0.5)
  topo = Topology()
  topo.construct_from_graph(G, AdHocNode, P2PFIFOFairLossChannel)
  for ch in topo.channels:
    topo.channels[ch].setPacketLossProbability(random.random())
    topo.channels[ch].setAverageNumberOfDuplicates(0)

  ComponentRegistry().print_components()

  topo.start()
  topo.plot()
  plt.show()  # while (True): pass

  print(topo.nodecolors)

if __name__ == "__main__":
  main()
