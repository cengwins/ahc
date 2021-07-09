import matplotlib.pyplot as plt
import networkx as nx
import random

from TagToTag.GenericTag import TagComponent, ReaderComponent, TagMessageDestinationIdentifiers, TagMessageTypes
from Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes, ConnectorTypes, Topology
from Channels import FIFOBroadcastFairLossChannel

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def on_message_from_top(self, eventobj: Event):
    # try:
    #   print("Outgoing Message From ", self.mainTagComponent.tag_id, ". Node, To: ", eventobj.eventcontent.header.messageto, ". Node")
    # except:
    #   print("Outgoing Message From ", self.mainReaderComponent.reader_id, ". Node, To: ", eventobj.eventcontent.header.messageto, ". Node")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    # try:
    #   print("Incoming Message From: ", eventobj.eventcontent.header.messagefrom, ". Node, To: ", self.mainTagComponent.tag_id, ". Node")
    # except:
    #   print("Incoming Message From: ", eventobj.eventcontent.header.messagefrom, ". Node, To: ", self.mainReaderComponent.reader_id, ". Node")
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid, node_info):
    if node_info["node_type"] == "tag":
      self.mainTagComponent = TagComponent("MainTagComponent", componentid, node_info["tag_id"])
      self.mainTagComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
      self.connect_me_to_component(ConnectorTypes.UP, self.mainTagComponent)

    elif node_info["node_type"] == "reader":
      self.mainReaderComponent = ReaderComponent("MainReaderComponent", componentid, node_info["reader_id"])
      self.mainReaderComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
      self.connect_me_to_component(ConnectorTypes.UP, self.mainReaderComponent)

    super().__init__(componentname, componentid)


def compare_channel_and_instance_number(channel, node_id_1, node_id_2):
  return set(channel.componentinstancenumber.split("-")) == {str(node_id_1), str(node_id_2)}

def disconnect_two_nodes(graph, topology, node_id_1, node_id_2):
  node_1_channels = topology.nodes[node_id_1].connectors[ConnectorTypes.DOWN]
  for channel_index in range(0, len(node_1_channels)):
    if compare_channel_and_instance_number(node_1_channels[channel_index], node_id_1, node_id_2):
      del node_1_channels[channel_index]
      break

  node_2_channels = topology.nodes[node_id_2].connectors[ConnectorTypes.DOWN]
  for channel_index in range(0, len(node_2_channels)):
    if compare_channel_and_instance_number(node_2_channels[channel_index], node_id_1, node_id_2):
      del node_2_channels[channel_index]
      break

  for channel in topology.channels:
    if compare_channel_and_instance_number(topology.channels[channel], node_id_1, node_id_2):
      del topology.channels[channel]
      break

  graph.remove_edge(node_id_1, node_id_2)

def connect_two_nodes(graph, topology, node_id_1, node_id_2, channeltype):
  ch = channeltype(channeltype.__name__, str(node_id_1) + "-" + str(node_id_2))
  topology.channels[(node_id_1, node_id_2)] = ch
  topology.nodes[node_id_1].connect_me_to_channel(ConnectorTypes.DOWN, ch)
  topology.nodes[node_id_2].connect_me_to_channel(ConnectorTypes.DOWN, ch)

  graph.add_edge(node_id_1, node_id_2)

node_count = 3

G = nx.random_geometric_graph(node_count, 1)
nx.draw(G, with_labels=True, font_weight='bold')

random_tc_1 = random.randint(10000000000, 99999999999)
random_tc_2 = random.randint(10000000000, 99999999999)
# node_info = {0: {"node_type": "reader", "reader_id": random_tc_1*10}, 1: {"node_type": "tag", "tag_id": random_tc_1*10+1}, 2: {"node_type": "tag", "tag_id": random_tc_2*10+2}, 3: {"node_type": "tag", "tag_id": random_tc_1*10+3}}
node_info = {0: {"node_type": "reader", "reader_id": random_tc_1*10}, 1: {"node_type": "tag", "tag_id": random_tc_1*10+1}, 2: {"node_type": "tag", "tag_id": random_tc_2*10+2}}
topo = Topology()
topo.construct_from_graph_with_node_info(G, AdHocNode, FIFOBroadcastFairLossChannel, node_info)
topo.start()

while 1:
  print("To change the graph exit first.")
  plt.show()
  choice = int(input("To add an edge -> 1\nTo remove an edge -> 2\nTo start reader -> 3\nTo exit -> 0\n"))
  if choice == 0:
    break
  if choice == 1:
    node_id_1 = int(input("Node ID 1: "))
    node_id_2 = int(input("Node ID 2: "))
    connect_two_nodes(G, topo, node_id_1, node_id_2, FIFOBroadcastFairLossChannel)
  elif choice == 2:
    node_id_1 = int(input("Node ID 1: "))
    node_id_2 = int(input("Node ID 2: "))
    disconnect_two_nodes(G, topo, node_id_1, node_id_2)
  elif choice == 3:
    reader_node_id = int(input("Reader Node ID: "))
    topo.nodes[reader_node_id].mainReaderComponent.start_collecting()
  nx.draw(G, with_labels=True, font_weight='bold')
