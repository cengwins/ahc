import random
import time
import networkx as nx
import matplotlib.pyplot as plt
from RoutingAODVABRComponent import AODV_ABRComponent

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels.Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer

registry = ComponentRegistry()
topo = Topology()


class AdHocNode(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.routing_aodv_abr = AODV_ABRComponent("AODV-ABR", componentid)
        self.link_layer = LinkLayer("LinkLayer", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.routing_aodv_abr.connect_me_to_component(ConnectorTypes.DOWN, self.link_layer)
        self.link_layer.connect_me_to_component(ConnectorTypes.UP, self.routing_aodv_abr)

        # Connect the bottom component to the composite component....
        self.link_layer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.link_layer)

        super().__init__(componentname, componentid)


def main():

    G = nx.random_geometric_graph(10, 0.5, seed=5)
    nx.draw(G, with_labels=True, font_weight='bold')
    plt.draw()
    topo = Topology()
    topo.construct_from_graph(G, AdHocNode, P2PFIFOPerfectChannel)
    topo.start()

    random.seed(10)
    source_node: AdHocNode = topo.get_node(0)
    dest_node: AdHocNode = topo.get_node(5)
    link_upstream_node: AdHocNode = topo.get_node(6)
    link_downstream_node: AdHocNode = topo.get_node(5)
    print('source node: ', source_node.componentinstancenumber)
    print('dest node: ', dest_node.componentinstancenumber)
    source_node.routing_aodv_abr.start_routing(source_node, dest_node)
    time.sleep(10)
    link_upstream_node.routing_aodv_abr.linkBreak(link_upstream_node, link_downstream_node, source_node, dest_node)
    plt.show()

    while (True): pass


if __name__ == "__main__":
    main()

