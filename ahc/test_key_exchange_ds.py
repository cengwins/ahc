from ahc.Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel
from ahc.Security.AKA.key_exchange_digital_signature import *
import networkx as nx




def main():
    edges = [(0, 1), (0, 2), (1, 2)]
    graph = nx.Graph()
    graph.add_edges_from(edges)
    nodes = [0,1,2]
    graph.add_nodes_from(nodes)
    topology = Topology()
    topology.construct_from_graph_key_exchange(graph, TrentNode, AliceNode, BobNode, P2PFIFOPerfectChannel)
    topology.start()
    topology.plot()

    while True: pass

if __name__ == "__main__":
    main()

