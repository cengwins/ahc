import threading
import logging
import time
from copy import deepcopy

from networkx import Graph
from typing import Dict, List, Any, Tuple

from ahc.Ahc import *
from ahc.Routing.STAR.MinHeap import MinHeap, MinHeapNode
from ahc.Routing.STAR.helper import STARStats, STARStatEvent

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] - %(message)s')
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class STARMessageTypes(Enum):
    NEIGHBOR_UP = "NeighborUp"
    LSU = "LinkStateUpdate"
    APP = "AppMessage"


class LSUMessage:
    def __init__(self, src: int, dest: int, link_cost: float, timestamp: int):
        self.src: int = src
        self.dest: int = dest
        self.link_cost: float = link_cost
        self.time: int = timestamp

    def __str__(self) -> str:
        return f"({self.src}, {self.dest}, {self.link_cost}, {self.time})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class STARNodeComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        """ Node initializes itself """
        super().__init__(componentname, componentinstancenumber)
        self.topology_graphs: Dict = {self.componentinstancenumber: nx.Graph()}
        self.source_trees: Dict = {self.componentinstancenumber: nx.DiGraph()}
        self.routing_table = {}
        self.neighbors: List[int] = []
        self.messages: List[Tuple[STARMessageTypes, Any]] = []
        self.message_handlers: Dict = {
            STARMessageTypes.NEIGHBOR_UP: self.on_neighbor_up,
            STARMessageTypes.LSU: self.on_lsu,
            STARMessageTypes.APP: self.on_app_message
        }
        self.stats = STARStats()

    def on_init(self, eventobj: Event):
        """ Node tells its neighbors it is up """
        logger.info(f"STAR Node init: {self.componentinstancenumber}. ")
        logger.debug(f"T{threading.get_native_id()} # {self.componentinstancenumber} is announcing")

        self.announce_node_up()

    def on_message_from_bottom(self, eventobj: Event):
        event_type = eventobj.eventcontent.header.messagetype
        message_from = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload.messagepayload

        logger.debug(f"#{self.componentinstancenumber} got message from {message_from} = {payload}")

        self.message_handlers[event_type](eventobj)

    def on_app_message(self, eventobj: Event):
        message = eventobj.eventcontent
        message_to = message.header.messageto

        if message_to == self.componentinstancenumber:
            # incoming message is for me
            self.stats.push(STARStatEvent.APP_MSG_RECV, message.payload.messagepayload)

            self.send_up(Event(self, EventTypes.MFRB, message))
        else:
            try:
                next_hop = self.routing_table[message_to][0]

                message.header.nexthop = next_hop
                logger.debug(f"T{threading.get_native_id()} #{self.componentinstancenumber} Next hop: {next_hop}")
                message.payload.messagepayload['hop_count'] += 1
                self.send_down(Event(self, EventTypes.MFRT, message))
            except KeyError:
                # destination is not existed in the routing table
                # drop the message
                logger.error(f'Destination {message_to} not found in node {self.componentinstancenumber}')

    def on_message_from_top(self, eventobj: Event):
        message = eventobj.eventcontent
        message_to = message.header.messageto

        try:
            next_hop = self.routing_table[message_to][0]
            message.header.nexthop = next_hop
            self.send_down(Event(self, EventTypes.MFRT, message))
        except KeyError:
            # destination is not existed in the routing table
            # drop the message
            logger.error(f'Destination {message_to} not found in node {self.componentinstancenumber}')

        self.stats.push(STARStatEvent.APP_MSG_SENT)

    def announce_node_up(self):
        payload = {"node_id": self.componentinstancenumber}
        self.add_message(STARMessageTypes.NEIGHBOR_UP, payload)
        self.broadcast_messages()

    def add_message(self, message_type: STARMessageTypes, payload: Any):
        msg = (message_type, payload)
        self.messages.append(msg)

    def broadcast_messages(self):
        if len(self.messages) > 0:
            message_type = self.messages[0][0]
            hdr = GenericMessageHeader(message_type, self.componentinstancenumber,
                                       MessageDestinationIdentifiers.NETWORKLAYERBROADCAST)
            payload = GenericMessagePayload(self.messages)

            if message_type == STARMessageTypes.LSU:
                self.stats.push(STARStatEvent.LSU_MSG_SENT, len(self.messages))
                self.stats.push(STARStatEvent.UPDATE_MSG_SENT, 1)

            self.send_down(Event(self, EventTypes.MFRT, GenericMessage(hdr, payload)))

        self.messages = []

    def on_neighbor_up(self, eventobj: Event):
        """ Node gets a NEIGHBOR_UP message and update its source tree and topology graph, and announce link update """

        message_from = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload.messagepayload

        if len(payload) == 0:
            return
        elif len(payload) == 1:
            node_id = message_from
            link_cost = Topology().G[node_id][self.componentinstancenumber]['weight']
        else:
            raise NotImplementedError()

        self.neighbors.append(node_id)
        self.topology_graphs[node_id] = nx.Graph()
        self.source_trees[node_id] = nx.DiGraph()
        send_st = True  # Report source tree changes

        # TODO LORA

        # Update
        lsu = LSUMessage(self.componentinstancenumber, node_id, link_cost, self.__now())
        self.update(self.componentinstancenumber, [lsu])

        if send_st:
            my_st: Graph = self.source_trees[self.componentinstancenumber]
            my_tg: Graph = self.topology_graphs[self.componentinstancenumber]
            self.messages = []

            for (u, v) in my_st.edges:
                l, t = my_tg[u][v]['weight'], my_tg[u][v]['time']
                lsu = LSUMessage(u, v, l, t)
                logger.debug(f"T{threading.get_native_id()} # {self.componentinstancenumber} is sending lsu {lsu}")
                self.add_message(STARMessageTypes.LSU, lsu)

            self.broadcast_messages()

    def on_lsu(self, eventobj: Event):
        self.stats.push(STARStatEvent.LSU_MSG_RECV, 1)
        message_from = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload.messagepayload

        # logger.debug(f"T{threading.get_native_id()} # {self.componentinstancenumber} is updating from lsu {payload}")

        self.update(message_from, payload)

    def update(self, k: int, payload: List[LSUMessage]):
        """ Process update message 'lsu' sent by router 'node_id' """
        self.update_topology_graph(k, payload)

        if k != self.componentinstancenumber:
            self.build_shortest_path_tree(k)

        self.build_shortest_path_tree(self.componentinstancenumber)
        self.update_routing_table()

        if k != self.componentinstancenumber:
            self.broadcast_messages()

    def update_topology_graph(self, k: int, payload: List[LSUMessage]):
        for lsu in payload:
            if type(lsu) == tuple:
                lsu = lsu[1]
            if lsu.link_cost != float("inf"):
                self.process_add_update(k, lsu)
            else:
                self.process_void_update(k, lsu)

    def build_shortest_path_tree(self, k: int):
        """ Construct source tree of node k """
        self.init_single_source(k)
        k_tg: Graph = self.topology_graphs[k]
        my_tg: Graph = self.topology_graphs[self.componentinstancenumber]
        min_heap = MinHeap()
        new_st = nx.DiGraph()

        for node in k_tg.nodes:
            min_heap.insert(MinHeapNode(node, k_tg.nodes[node]))

        popped_node: MinHeapNode = min_heap.extract_min()
        d, u, u_data = popped_node.data['d'], popped_node.key, popped_node.data

        while u_data is not None and u_data['d'] < float('inf'):
            pred = u_data['pred']

            if pred is not None and not new_st.has_edge(pred[0], pred[1]):
                new_st.add_edge(pred[0], pred[1], weight=pred[2]['weight'], time=pred[2]['time'], dlt=pred[2]['dlt'])

            adj_list = {n: nbrdict for n, nbrdict in k_tg.adjacency()}

            for v in adj_list[u]:
                cond_1 = k_tg.has_edge(u, v) or k_tg[u][v]['weight'] != float('inf')
                cond_2 = my_tg.has_edge(u, v) and not my_tg[u][v]['dlt']

                if cond_1 and cond_2:
                    pass
                else:
                    continue

                if k == self.componentinstancenumber:
                    if u == self.componentinstancenumber:
                        suc = self.componentinstancenumber
                    elif my_tg.nodes[u]['suc'] == self.componentinstancenumber:
                        suc = u
                    else:
                        suc = my_tg.nodes[u]['suc']
                else:
                    if u == k:
                        if v == self.componentinstancenumber:
                            suc = self.componentinstancenumber
                        else:
                            suc = k
                    else:
                        try:
                            suc = my_tg.nodes[u]['suc']
                        except KeyError:
                            suc = None

                self.relax_edge(k, u, v, min_heap, suc)

            if not min_heap.is_empty():
                popped_node: MinHeapNode = min_heap.extract_min()
                d, u, u_data = popped_node.data['d'], popped_node.key, popped_node.data
            else:
                d, u, u_data = None, None, None

        self.update_neighbor_tree(k, new_st)

        if k == self.componentinstancenumber:
            # TODO LORA
            self.report_changes(self.source_trees[self.componentinstancenumber], new_st)
            my_tg_edges = deepcopy(my_tg.edges)

            for (u, v) in my_tg_edges:
                if my_tg[u][v]['dlt']:
                    my_tg.remove_edge(u, v)

        self.source_trees[k] = new_st

    def update_routing_table(self):
        my_st = self.source_trees[self.componentinstancenumber]

        for dest in my_st.nodes:
            if dest != self.componentinstancenumber:
                path = nx.dijkstra_path(my_st, self.componentinstancenumber, dest)
                length = nx.dijkstra_path_length(my_st, self.componentinstancenumber, dest)
                self.routing_table[dest] = (path[1], length)

    def process_add_update(self, k: int, lsu: LSUMessage):
        """ Update topology graphs of this node and the neighbor from 'lsu' """
        my_tg: Graph = self.topology_graphs[self.componentinstancenumber]
        edge_existed = my_tg.has_edge(lsu.src, lsu.dest)

        if not edge_existed or lsu.time > my_tg[lsu.src][lsu.dest]['time']:
            if not edge_existed:
                my_tg.add_edge(lsu.src, lsu.dest, weight=lsu.link_cost, time=lsu.time, dlt=False)
            else:
                my_tg[lsu.src][lsu.dest]['weight'] = lsu.link_cost
                my_tg[lsu.src][lsu.dest]['time'] = lsu.time

        if k != self.componentinstancenumber:
            k_tg: Graph = self.topology_graphs[k]
            k_tg_edges = deepcopy(k_tg.edges)
            for (r, s) in k_tg_edges:
                if r != lsu.src and s == lsu.dest:
                    k_tg.remove_edge(r, s)

            if not k_tg.has_edge(lsu.src, lsu.dest):
                k_tg.add_edge(lsu.src, lsu.dest, weight=lsu.link_cost, time=lsu.time, dlt=False)
            else:
                k_tg[lsu.src][lsu.dest]['weight'] = lsu.link_cost
                k_tg[lsu.src][lsu.dest]['time'] = lsu.time

        my_tg[lsu.src][lsu.dest]['dlt'] = False

    def process_void_update(self, k: int, lsu: LSUMessage):
        # TODO on link failure
        pass

    def init_single_source(self, k: int):
        k_tg: Graph = self.topology_graphs[k]

        for v in k_tg.nodes:
            k_tg.nodes[v]['d'] = float('inf')
            k_tg.nodes[v]['pred'] = None
            try:
                k_tg.nodes[v]['sucp'] = k_tg.nodes[v]['suc']
            except KeyError:
                k_tg.nodes[v]['sucp'] = None
            k_tg.nodes[v]['suc'] = None
            k_tg.nodes[v]['nbr'] = None

        k_tg.nodes[k]['d'] = 0

    def relax_edge(self, k: int, u: int, v: int, min_heap: MinHeap, suc: int):
        k_tg: Graph = self.topology_graphs[k]
        my_st: Graph = self.source_trees[self.componentinstancenumber]

        COND_1 = k_tg.nodes[v]['d'] > k_tg.nodes[u]['d'] + k_tg[u][v]['weight']

        COND_2 = k == self.componentinstancenumber and \
                 k_tg.nodes[v]['d'] == k_tg.nodes[u]['d'] + k_tg[u][v]['weight'] and \
                 my_st.has_edge(u, v)

        if COND_1 or COND_2:
            k_tg.nodes[v]['d'] = k_tg.nodes[u]['d'] + k_tg[u][v]['weight']
            k_tg.nodes[v]['pred'] = (u, v, k_tg[u][v])
            k_tg.nodes[v]['suc'] = suc

            # TODO LORA

            min_heap.insert(MinHeapNode(v, k_tg.nodes[v]))

    def update_neighbor_tree(self, k: int, new_st: Graph):
        """ Delete links from k's topology graph and report failed links"""
        k_tg: Graph = self.topology_graphs[k]
        k_st: Graph = self.source_trees[k]
        k_st_edges = deepcopy(k_st.edges)
        my_tg: Graph = self.topology_graphs[self.componentinstancenumber]

        for (u, v) in k_st_edges:
            if not new_st.has_edge(u, v):
                # k has removed (u, v) from its source tree
                # TODO LORA
                if k == self.componentinstancenumber and \
                        (u == self.componentinstancenumber or my_tg.nodes[v]['pred'] is None):
                    # i has no path to destination v or i is the head node
                    if my_tg.nodes[v]['pred'] is None:
                        for (r, s) in my_tg.edges:
                            if s == v:
                                if not my_tg.has_edge(r, s) or my_tg[r][s]['weight'] == float('inf'):
                                    l = my_tg[r][s]['weight']
                                    t = my_tg[r][s]['time']
                                    lsu = LSUMessage(r, s, l, t)
                                    self.add_message(STARMessageTypes.LSU, lsu)
                    elif not my_tg.has_edge(u, v) or my_tg[u][v]['weight'] == float('inf'):
                        l = my_tg[u][v]['weight']
                        t = my_tg[u][v]['time']
                        lsu = LSUMessage(u, v, l, t)
                        self.add_message(STARMessageTypes.LSU, lsu)
                if not (k == self.componentinstancenumber and u == self.componentinstancenumber):
                    if k_tg.has_edge(u, v):
                        k_tg.remove_edge(u, v)

                    if my_tg.has_edge(u, v) and my_tg[u][v]['weight'] != float('inf'):
                        for x in self.neighbors:
                            x_tg: Graph = self.topology_graphs[x]
                            if x_tg.has_edge(u, v):
                                return
                        my_tg[u][v]['dlt'] = True

    def report_changes(self, old_st: Graph, new_st: Graph):
        """ Generate new LSUs for new links in the router's source tree """
        my_tg: Graph = self.topology_graphs[self.componentinstancenumber]

        for (u, v) in new_st.edges:
            if not old_st.has_edge(u, v) or \
                    new_st[u][v]['time'] != old_st[u][v]['time']:
                try:
                    l = my_tg[u][v]['weight']
                    t = my_tg[u][v]['time']

                    lsu = LSUMessage(u, v, l, t)
                    self.add_message(STARMessageTypes.LSU, lsu)
                except KeyError:
                    pass

    def __now(self):
        return time.time_ns() // 1000

    def plot(self, gg: Graph):
        import matplotlib.pyplot as plt
        nodepos = nx.drawing.spring_layout(gg)
        nodecolors = ['#6aff20'] * len(gg.nodes)
        nx.draw(gg, nodepos, node_color=nodecolors, with_labels=True, font_weight='bold')

        labels = nx.get_edge_attributes(gg, 'weight')
        nx.draw_networkx_edge_labels(gg, nodepos, edge_labels=labels)

        plt.show()

    def show_routing_table(self):
        print(f'{self.componentinstancenumber} => {self.routing_table}')

    def show_topology_graph(self, k):
        self.plot(self.topology_graphs[k])

    def show_source_tree(self, k):
        self.plot(self.source_trees[k])
