import random
import time
from threading import Thread

import matplotlib.pyplot as plt
import networkx as nx

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessage, GenericMessageHeader
from Ahc import ComponentRegistry
from Broadcasting.Broadcasting import ControlledFlooding
from Channels import P2PFIFOFairLossChannel, Channel, BasicLossyChannel
from Consensus.raft_component import ConsensusComponent, RaftConsensusComponent
from LinkLayers.GenericLinkLayer import LinkLayer
from itertools import combinations

registry = ComponentRegistry()


class AdHocNode(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        time.sleep(0.1)
        print("received event from", eventobj.eventsource.componentinstancenumber)
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent + self.componentinstancenumber))

    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)


#    self.eventhandlers[EventTypes.MFRT] = self.onMessageFromTop
#    self.eventhandlers["messagefromchannel"] = self.onMessageFromChannel

class Client:

    def send(self, message):
        print(tuple(message))


def main():
    nodes = ['A', 'B', 'C', 'D', 'E']
    #nodes = ['A', 'B', 'C']
    # nodes = ['A', 'B']

    edges = combinations(nodes, 2)
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    topo = Topology()
    topo.construct_from_graph(G, RaftConsensusComponent, BasicLossyChannel)
    client = Client()

    topo.start()
    time.sleep(5)
    a_node: RaftConsensusComponent = topo.nodes.get('A')
    cluster = a_node.registry.get_non_channel_components()
    a_node = topo.nodes.get(cluster[0].state.leaderId)
    a_node.data_received_client(client, {'type':'append',  'data': {
                                      'key': 'hello',
                                      'value': 'hello',}})
    a_node.data_received_client(client, {'type':'append',  'data': {
                                      'key': 'hello',
                                      'value': 'hello',}})
    waitforit = input("hit something to exit...")


if __name__ == "__main__":
    main()
