import networkx as nx
import yaml as ym

from .Parser import AhcObject

class Experiment:
    AhcObj = AhcObject()

    def construct_from_nx_graph(self, graph: nx.Graph, node_type):
        pass

    def construct_from_graph(self, graph, node_type):
        pass

    def construct_from_dict(self, dict: dict):
        pass

    def construct_from_yaml(self, yaml):
        AhcObject.parse_data(yaml)




