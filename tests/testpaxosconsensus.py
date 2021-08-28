import sys
import time

import networkx as nx

from Ahc import Topology
from Ahc import ComponentRegistry
from PhysicalLayers.Channels import BasicLossyChannel
from Consensus.Paxos.paxos_component import PaxosConsensusComponentModel, Resolution
from itertools import combinations
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)

registry = ComponentRegistry()

class Client:

    def send(self, message:Resolution):
        logger.info("For client Resolution message is received from component %s",
                    message.from_uid.componentinstancenumber)
        logger.info("Client received new set value %s", message.value)


def main():
    nodes = ['A', 'B', 'C', 'D', 'E']

    edges = combinations(nodes, 2)
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    topo = Topology()
    topo.construct_from_graph(G, PaxosConsensusComponentModel, BasicLossyChannel)
    client = Client()

    topo.start()
    time.sleep(2)
    a_node: PaxosConsensusComponentModel = topo.nodes.get('A')
    a_node.data_received_client(client, "Hello World!!!")
    waitforit = input("hit something to exit...")


if __name__ == "__main__":
    main()
