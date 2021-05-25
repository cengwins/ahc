import random
import time
from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from TagToTag.GenericTag_ChandyMisra import TagComponent, TagMessageDestinationIdentifiers, TagMessageTypes
from Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes, ConnectorTypes, Topology, ComponentRegistry, registry
from Channels import TagToTagFIFOPerfectChannel

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    # print("Outgoing Message from ", self.componentinstancenumber, ". Node", ", via channel: [", eventobj.eventcontent.header.interfaceid, "]")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    # print("Incoming Message to ", self.componentinstancenumber, ". Node, From: ", eventobj.eventcontent.header.messagefrom)
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):

    # SUBCOMPONENTS
    self.mainTagComponent = TagComponent("MainTagComponent", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS

    # Connect the bottom component to the composite component....
    self.mainTagComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.mainTagComponent)

    super().__init__(componentname, componentid)

def draw_randow_geometric_graph_with_edge_weight(node_count, radius, max_weight):
  G = nx.random_geometric_graph(node_count, radius)
  edges = list(G.edges)
  for edge in edges:
    random_weight = random.randint(1, max_weight)
    G[edge[0]][edge[1]]['weight'] = random_weight
    G[edge[1]][edge[0]]['weight'] = random_weight
  node_positions = nx.get_node_attributes(G, 'pos')
  node_labels = {node:node for node in G.nodes()}
  edge_labels = nx.get_edge_attributes(G, 'weight')
  nx.draw(G, node_positions, edge_color='black', node_color='blue', labels=node_labels)
  nx.draw_networkx_edge_labels(G, node_positions, edge_labels=edge_labels, font_color='red')
  return G

node_count = 5
radius = 0.8
max_weight = 10

G = draw_randow_geometric_graph_with_edge_weight(node_count, radius, max_weight)

topo = Topology()
topo.construct_from_weighted_graph(G, AdHocNode, TagToTagFIFOPerfectChannel)
topo.start()

initiator_tag_id = 0
topo.nodes[initiator_tag_id].mainTagComponent.start_initiator()

time.sleep(3)

starting_time = topo.nodes[initiator_tag_id].mainTagComponent.starting_message_timestamp
last_incoming_message_timestamp = topo.nodes[initiator_tag_id].mainTagComponent.starting_message_timestamp

for n in topo.nodes:
  if topo.nodes[n].mainTagComponent.initial_parent == None:
    if n == initiator_tag_id:
      if topo.nodes[n].mainTagComponent.last_incoming_message_timestamp > last_incoming_message_timestamp:
        last_incoming_message_timestamp = topo.nodes[n].mainTagComponent.last_incoming_message_timestamp
      print(n, ": (Distance: ", topo.nodes[n].mainTagComponent.initial_distance, ", Parent: Initiator Tag)")
    else:
      print(n, ": (Distance: ", topo.nodes[n].mainTagComponent.initial_distance, ", Parent: None) [Unreached Node]")
  else:
    if topo.nodes[n].mainTagComponent.last_incoming_message_timestamp > last_incoming_message_timestamp:
      last_incoming_message_timestamp = topo.nodes[n].mainTagComponent.last_incoming_message_timestamp
    print(n, ": (Distance: ", topo.nodes[n].mainTagComponent.initial_distance, ", Parent: ", topo.nodes[n].mainTagComponent.initial_parent, ")")

time_difference = last_incoming_message_timestamp - starting_time
print("Time Difference: ", time_difference)

plt.show()
