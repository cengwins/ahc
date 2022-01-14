import random
import networkx as nx
from threading import Thread, Event
from datetime import datetime

from ahc.Ahc import singleton


def random_undirected_graph(n):
    tries = 1000
    for i in range(tries):
        g = nx.gnp_random_graph(n, 0.2)
        if nx.is_connected(g):
            return g
    raise nx.NetworkXError("Maximum number of tries exceeded")


def random_directed_graph(n):
    g = random_undirected_graph(n).to_directed()
    # we can also sprinkle some directed edges
    # gd = nx.gnp_random_graph(n, 0.01, None, True)
    # for (u, v) in gd.edges:
    #    g.add_edge(u, v)
    return g


def random_layered_graph(n):
    def make_layer(mp):
        g = random_undirected_graph(len(mp))
        gs = nx.Graph()
        for (su, sv) in g.edges:
            gs.add_edge(mp[su], mp[sv])
        return gs
    i = list(range(n))
    random.shuffle(i)
    #  0- 50 => {1}
    # 50- 80 => {1,2}
    # 80- 90 =>   {2,3}
    # 90-100 =>     {3}
    sep = [make_layer(i[:int(.8*n)]),
           make_layer(i[int(.5*n):int(.9*n)]),
           make_layer(i[int(.7*n):])]
    g = nx.Graph()
    node_layers = {}
    for layer in range(len(sep)):
        for (u, v) in sep[layer].edges:
            g.add_edge(u, v)
            if u not in node_layers:
                node_layers[u] = set()
            node_layers[u].add(layer)
            if v not in node_layers:
                node_layers[v] = set()
            node_layers[v].add(layer)
    for k, v in node_layers.items():
        g.add_node(k, conf={'layers': v})
    return g, sep

def keys_to_set(m):
    s = set()
    for n in m.keys():
        s.add(n)
    return s


@singleton
class Tracing:
    nodes = set()
    node_address_to_id = {}
    node_edges = {}
    node_edges_each_step = []

    def register_node(self, address, node_id):
        self.nodes.add(node_id)
        self.node_address_to_id[address] = node_id

    def update_edges(self, edges):
        current_time = datetime.now()
        ne = {}
        for k, v in self.node_edges.items():
            ne[k] = v
        for (from_addr, to_addr) in edges:
            from_id = self.node_address_to_id[from_addr]
            to_id = self.node_address_to_id[to_addr]
            attr = {'received_at': current_time}
            ne[(from_id, to_id)] = attr
        if keys_to_set(self.node_edges) != keys_to_set(ne):
            self.node_edges_each_step.append(ne)
        self.node_edges = ne

    def to_graph(self):
        edges = []
        for (f, t), a in self.node_edges.items():
            edges.append((f, t, a))
        graph = nx.Graph()
        graph.add_nodes_from(self.nodes)
        graph.add_edges_from(edges)
        return graph

    def step_to_graph(self, step):
        edges = []
        if step >= len(self.node_edges_each_step):
            step = len(self.node_edges_each_step) - 1
        for (f, t), a in self.node_edges_each_step[step].items():
            edges.append((f, t, a))
        graph = nx.Graph()
        graph.add_nodes_from(self.nodes)
        graph.add_edges_from(edges)
        return graph


@singleton
class RepeatDeltaTimer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.interval = 1.0
        self.finished = Event()
        self.functions = []

    def set_interval(self, interval):
        self.interval = interval

    def register_function(self, fn):
        self.functions.append(fn)

    def cancel(self):
        self.finished.set()

    def run(self):
        prev_time = datetime.now()
        while not self.finished.wait(self.interval):
            current_time = datetime.now()
            delta = current_time - prev_time
            prev_time = current_time
            for f in self.functions:
                f(current_time, delta.total_seconds())
