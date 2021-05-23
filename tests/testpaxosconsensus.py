import time

import networkx as nx

from Ahc import Topology
from Ahc import ComponentRegistry
from Channels import BasicLossyChannel
from Consensus.Paxos.paxos_component import PaxosConsensusComponentModel
from Consensus.Raft.raft_component import RaftConsensusComponent
from itertools import combinations

registry = ComponentRegistry()

class Client:

    def send(self, message):
        print(tuple(message))


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
    a_node.data_received_client(client, "message")
    waitforit = input("hit something to exit...")


if __name__ == "__main__":
    main()
