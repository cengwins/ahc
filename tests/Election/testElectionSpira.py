import os
import sys
import time
from enum import Enum
from graph import *
import numpy  as np
sys.path.insert(0, os.getcwd())

import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Election.Spira import ElectionSpiraComponent

registry = ComponentRegistry()


class AdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def initialize(self):
        self.appllayer.initialize_connect()

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = ElectionSpiraComponent("ElectionSpiraComponent", componentid)
        self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
        super().__init__(componentname, componentid)


topo = Topology()
message_count = 0


def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    global message_count
    fig, axes = plt.subplots(1, 2)
    fig.set_figheight(5)
    fig.set_figwidth(10)
    fig.tight_layout()

    time_arr = []
    message_arr = []

    for i in range(4, 9):

        start_time = time.time()

        g = Grid(i, ax=axes[0])
        topo.construct_from_graph(g.G, AdHocNode, P2PFIFOPerfectChannel)
        topo.start()
        for i in list(topo.nodes):
            topo.nodes[i].initialize()

        end_time = time.time()
        time_arr.append(end_time - start_time)

        message_arr.append(message_count)
        message_count = 0
        # g.plot()
    axes[0].plot(np.array([n ** 2 for n in range(4, 9)]), np.array(message_arr))
    axes[1].plot(np.array([n ** 2 for n in range(4, 9)]), np.array(time_arr))
    axes[0].set_ylabel('Messeage Count')
    axes[0].set_xlabel('Node Count')
    axes[1].set_ylabel('Time Passes in Seconds')
    axes[1].set_xlabel('Node Count')
    axes[0].set_title("Message Count by Node Count")
    axes[1].set_title("Time")
    # axes[1,0].set_title("Time Passed for execution of Gallager-Humblet-Spira algorithm")
    print(time_arr)
    print(message_arr)
    plt.show()
    # plt.show()  # while (True): pass


if __name__ == "__main__":
    main()