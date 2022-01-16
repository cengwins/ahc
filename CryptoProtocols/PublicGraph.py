import random
import networkx as nx
import numpy as np
from cryptography.hazmat.primitives.ciphers import CipherContext


class PublicGraph:
    def __generate_graph_with_hamiltonian_cycle(self, graph_node_size, cycle_node_size):
        # init public graph and its hamiltonian cycle
        public_graph = nx.Graph()
        hamiltonian_cycle = nx.Graph()
        # calculate cycle start node
        cycle_start_node = int(np.ceil((graph_node_size - cycle_node_size) / 2))
        # add all nodes to both graph and to cycle
        public_graph.add_nodes_from(range(0, graph_node_size))
        hamiltonian_cycle.add_nodes_from(range(cycle_start_node, cycle_start_node + cycle_node_size))
        # loop through to form cycle
        for i in range(cycle_start_node, cycle_start_node + cycle_node_size - 1):
            public_graph.add_edge(i, i + 1, attr=True)
            hamiltonian_cycle.add_edge(i, i + 1, attr=True)
        # connect last node with the starting node
        public_graph.add_edge(cycle_start_node + cycle_node_size - 1, cycle_start_node, attr=True)
        hamiltonian_cycle.add_edge(cycle_start_node + cycle_node_size - 1, cycle_start_node, attr=True)
        # loop through to add confusion edges to form the public graph
        for i in range(graph_node_size):
            for j in range(i + 1, graph_node_size):
                if (i, j) not in list(public_graph.edges) and random.uniform(0, 1) > 0.5:
                    # add edge if edge is already not added and with probability
                    public_graph.add_edge(i, j, attr=True)

        """
        # uncomment to view graph and hamiltonian cycle
        print("Formed Hamiltonian Cycle\n", nx.to_numpy_matrix(hamiltonian_cycle,
                                                               nodelist=[*range(cycle_start_node,
                                                                                cycle_start_node + cycle_node_size)]))
        print("Formed Public Graph\n", nx.to_numpy_matrix(public_graph,
                                                          nodelist=[*range(0, 0 + graph_node_size)]))
        """

        return public_graph, hamiltonian_cycle, cycle_start_node

    @staticmethod
    def get_graph():
        return PublicGraph.__GRAPH

    @staticmethod
    def get_hamiltonian_cycle(auth_keyword):
        # This method is abstract, it is used to give intuition that prover knows the cycle
        if auth_keyword == PublicGraph.__AUTH_KEYWORD:
            return PublicGraph.__HAMILTONIAN_CYCLE
        return None

    @staticmethod
    def get_graph_no_nodes():
        shape = nx.to_numpy_matrix(PublicGraph.__GRAPH).shape
        return shape[0]

    @staticmethod
    def get_graph_matrix_size():
        shape = nx.to_numpy_matrix(PublicGraph.__GRAPH).shape
        return shape[0] * shape[1]

    @staticmethod
    def get_hamiltonian_cycle_no_nodes(auth_keyword):
        # This method is abstract, it is used to give intuition that prover knows the cycle
        if auth_keyword == PublicGraph.__AUTH_KEYWORD:
            shape = nx.to_numpy_matrix(PublicGraph.__HAMILTONIAN_CYCLE).shape
            return shape[0]
        return None

    @staticmethod
    def get_hamiltonian_cycle_matrix_size(auth_keyword):
        # This method is abstract, it is used to give intuition that prover knows the cycle
        if auth_keyword == PublicGraph.__AUTH_KEYWORD:
            shape = nx.to_numpy_matrix(PublicGraph.__HAMILTONIAN_CYCLE).shape
            return shape[0] * shape[1]
        return None

    @staticmethod
    def get_hamiltonian_cycle_start_node(auth_keyword):
        # This method is abstract, it is used to give intuition that prover knows the cycle
        if auth_keyword == PublicGraph.__AUTH_KEYWORD:
            return PublicGraph.__CYCLE_START_NODE
        return None

    # To use normal implementation make graph_node_size = cycle_node_size
    # To hide a cycle in a larger graph make graph_node_size >= cycle_node_size
    __GRAPH, __HAMILTONIAN_CYCLE, __CYCLE_START_NODE = __generate_graph_with_hamiltonian_cycle(self=None,
                                                                                               graph_node_size=10,
                                                                                               cycle_node_size=10)
    # This keyword is abstract, it is used to give intuition that prover knows the cycle
    __AUTH_KEYWORD = "BearsBeetsBattleStarGalactica"


class PublicGraphHelper:
    @staticmethod
    def convert_cypher_graph_to_bytes(graph):
        graph_bytes = b""
        for i in range(graph.shape[0]):
            for j in range(graph.shape[1]):
                graph_bytes += graph[i, j]
        """
        # uncomment to view graph and hamiltonian cycle
        print("Str graph", graph_bytes)
        """
        return graph_bytes

    @staticmethod
    def convert_bytes_to_cypher_graph(graph_bytes):
        graph_no_nodes = PublicGraph.get_graph_no_nodes()
        matrix = np.asmatrix(np.zeros((graph_no_nodes, graph_no_nodes), dtype=CipherContext))
        tmp_graph_bytes = graph_bytes
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                tmp_edge_bytes = tmp_graph_bytes[0:4]
                tmp_graph_bytes = tmp_graph_bytes[4:]
                matrix[i, j] = tmp_edge_bytes
        """
        # uncomment to view graph and hamiltonian cycle
        print("Graph Redesigned\n", matrix)
        """
        return matrix

    @staticmethod
    def permute_graph(graph, no_nodes):
        # get public graph
        nodes = [*range(0, no_nodes)]
        shuffled_nodes = random.sample(nodes, len(nodes))
        node_mapping = {}
        # form node mapping
        for i in range(len(nodes)):
            node_mapping[i] = shuffled_nodes[i]
        # return permuted graph with node mapping
        permuted_graph = nx.relabel_nodes(graph, node_mapping)
        return permuted_graph, node_mapping

    @staticmethod
    def is_equal_to_public_graph(graph, node_mapping):
        public_graph = PublicGraph.get_graph()
        permuted_graph = nx.relabel_nodes(public_graph, node_mapping)
        permuted_matrix = nx.to_numpy_matrix(permuted_graph, nodelist=[*range(0, PublicGraph.get_graph_no_nodes())])
        matrix = nx.to_numpy_matrix(graph, nodelist=[*range(0, PublicGraph.get_graph_no_nodes())])
        for i in range(permuted_matrix.shape[0]):
            for j in range(permuted_matrix.shape[1]):
                try:
                    if permuted_matrix[i, j] != matrix[i, j]:
                        return False
                except IndexError:
                    return False
        return True

    @staticmethod
    def is_symmetric_graph(graph_matrix):
        no_nodes = graph_matrix.shape[0]
        for i in range(no_nodes):
            for j in range(i, no_nodes):
                if graph_matrix[i, j] != graph_matrix[j, i]:
                    return False
        return True

    @staticmethod
    def graph_has_cycle(graph):
        no_nodes = PublicGraph.get_graph_no_nodes()
        graph_matrix = nx.to_numpy_matrix(graph, nodelist=[*range(0, no_nodes)])
        if not PublicGraphHelper.is_symmetric_graph(graph_matrix):
            # first check if graph is symmetric, if not undirected return false
            return False
        no_nodes = len(graph.nodes)
        visited_nodes = np.zeros((no_nodes,), dtype=bool)
        # nodes initialized to default value
        start_node = prev_node = current_node = -1
        # loop through to find the start node
        for i in range(no_nodes):
            for j in range(no_nodes):
                if graph_matrix[i, j] == 1:
                    start_node = i
                    prev_node = i
                    current_node = j
                    visited_nodes[start_node] = True
                    break
            if start_node > -1:
                break
        if start_node == -1:
            # if no node is start node, then empty graph, no cycle
            return False
        # loop through to check cycle
        while True:
            is_connected = False
            for i in range(no_nodes):
                if i != prev_node and graph_matrix[current_node, i] == 1:
                    # if edge found and not to the previous node
                    if start_node == i:
                        # if starting node reached we have cycle return true
                        return True
                    elif visited_nodes[i]:
                        # if already visited node and not start node return false
                        return False
                    else:
                        # if new node, update prev node and current node, mark as visited
                        is_connected = True
                        prev_node = current_node
                        current_node = i
                        visited_nodes[current_node] = True
                        break
            if not is_connected:
                # if the selected node is not connected to any node, no cycle possible
                return False


class FakeGraphHelper:
    @staticmethod
    def get_public_graph_with_fake_cycle():
        # init public graph and with no hamiltonian cycle
        public_graph = PublicGraph.get_graph().copy()
        fake_hamiltonian_cycle = PublicGraph.get_hamiltonian_cycle(FakeGraphHelper.__AUTH_KEYWORD).copy()
        graph_node_size = PublicGraph.get_graph_no_nodes()
        cycle_node_size = PublicGraph.get_hamiltonian_cycle_no_nodes(FakeGraphHelper.__AUTH_KEYWORD)
        # calculate cycle start node
        cycle_start_node = PublicGraph.get_hamiltonian_cycle_start_node(FakeGraphHelper.__AUTH_KEYWORD)
        # remove random edge from hamiltonian cycle
        removed_edge = list(fake_hamiltonian_cycle.edges)[0]
        fake_hamiltonian_cycle.remove_edge(removed_edge[0], removed_edge[1])
        """
        # uncomment to view graph and hamiltonian cycle
        print("Formed Hamiltonian Cycle\n", nx.to_numpy_matrix(fake_hamiltonian_cycle,
                                                               nodelist=[*range(cycle_start_node,
                                                                                cycle_start_node + cycle_node_size)]))
        print("Formed Public Graph\n", nx.to_numpy_matrix(public_graph,
                                                          nodelist=[*range(0, 0 + graph_node_size)]))
        """

        return public_graph, fake_hamiltonian_cycle, cycle_start_node

    @staticmethod
    def get_fake_public_graph():
        # init fake public graph and its hamiltonian cycle
        public_graph = PublicGraph.get_graph().copy()
        fake_hamiltonian_cycle = PublicGraph.get_hamiltonian_cycle(FakeGraphHelper.__AUTH_KEYWORD).copy()
        graph_node_size = PublicGraph.get_graph_no_nodes()
        cycle_node_size = PublicGraph.get_hamiltonian_cycle_no_nodes(FakeGraphHelper.__AUTH_KEYWORD)
        # calculate cycle start node
        cycle_start_node = PublicGraph.get_hamiltonian_cycle_start_node(FakeGraphHelper.__AUTH_KEYWORD)
        counter = 0
        # loop through to add confusion edges to form the public graph
        for i in range(graph_node_size):
            for j in range(i + 1, graph_node_size):
                if (i, j) not in list(public_graph.edges):
                    # add edge if edge is already not added and with probability
                    counter += 1
                    public_graph.add_edge(i, j, attr=True)
                    if counter >= FakeGraphHelper.__MAX_FAKE_EDGE_NO:
                        break
            if counter >= FakeGraphHelper.__MAX_FAKE_EDGE_NO:
                break
        """
        # uncomment to view graph and hamiltonian cycle
        print("Formed Hamiltonian Cycle\n", nx.to_numpy_matrix(fake_hamiltonian_cycle,
                                                               nodelist=[*range(cycle_start_node,
                                                                                cycle_start_node + cycle_node_size)]))
        print("Formed Public Graph\n", nx.to_numpy_matrix(public_graph,
                                                          nodelist=[*range(0, 0 + graph_node_size)]))
        """

        return public_graph, fake_hamiltonian_cycle, cycle_start_node

    __MAX_FAKE_EDGE_NO = 10
    __AUTH_KEYWORD = "BearsBeetsBattleStarGalactica"
