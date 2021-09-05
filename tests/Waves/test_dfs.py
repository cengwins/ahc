import os
import sys
import random
import time

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from Ahc import ComponentRegistry
from Waves.DepthFirstSearch import DfsTraverse
from Channels.Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer

registry = ComponentRegistry()

class AdHocNode(ComponentModel):
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.traverse_service = DfsTraverse("DfsTraverse", componentid)
    self.link_layer = LinkLayer("LinkLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.traverse_service.connect_me_to_component(ConnectorTypes.DOWN, self.link_layer)
    self.link_layer.connect_me_to_component(ConnectorTypes.UP, self.traverse_service)

    # Connect the bottom component to the composite component....
    self.link_layer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.link_layer)

    super().__init__(componentname, componentid)

def main():
  G = nx.random_geometric_graph(9, 0.5, seed=5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()
  topo = Topology()
  topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)

  topo.start()
  time.sleep(1)
  
  random.seed(10)
  random_node:AdHocNode = topo.get_random_node()
  random_node.traverse_service.start_traverse()
  plt.show()

  while (True): pass

if __name__ == "__main__":
  main()
