import random

from Ahc import *


class STARMessageTypes(Enum):
    NEIGHBOR_UP = "NeighborUp"
    LSU = "LinkStateUpdate"


class LSUMessage:
    def __init__(self, src, dest, link_cost, timestamp):
        self.src = src
        self.dest = dest
        self.link_cost = link_cost
        self.timestamp = timestamp


# nx.dijkstra_path(G, source, target)


class STARNodeComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.topology_graphs = {self.componentinstancenumber: nx.DiGraph()}
        self.source_trees = {self.componentinstancenumber: nx.DiGraph()}
        self.routing_table = []
        self.neighbors = []
        self.clock = 0
        self.st_last_reported = None
        self.messages = []
        self.message_handlers = {
            STARMessageTypes.NEIGHBOR_UP: self.__on_neighbor_up,
            STARMessageTypes.LSU: self.__on_lsu
        }

    def on_init(self, eventobj: Event):
        self.__announce_node_up()

    def on_message_from_bottom(self, eventobj: Event):
        event_type = eventobj.eventcontent.header.messagetype
        self.message_handlers[event_type](eventobj.eventcontent.payload.messagepayload)

    def on_message_from_top(self, eventobj: Event):
        pass

    def __announce_node_up(self):
        link_cost = random.randint(0, 10)
        payload = {"node_id": self.componentinstancenumber, "link_cost": link_cost}
        self.__add_message(STARMessageTypes.NEIGHBOR_UP, payload)
        self.__broadcast_messages()

    def __add_message(self, message_type: STARMessageTypes, payload):
        hdr = GenericMessageHeader(message_type, self.componentinstancenumber,
                                   MessageDestinationIdentifiers.NETWORKLAYERBROADCAST)
        payload = GenericMessagePayload(payload)
        self.messages.append(GenericMessage(hdr, payload))

    def __broadcast_messages(self):
        for i, msg in enumerate(self.messages):
            self.send_down(Event(self, EventTypes.MFRT, msg))
            del self.messages[i]

    def __on_neighbor_up(self, payload):
        node_id, link_cost = payload["node_id"], payload["link_cost"]
        self.neighbors.append(node_id)
        self.topology_graphs[node_id] = nx.DiGraph()
        self.source_trees[node_id] = nx.DiGraph()
        send_st = True  # Report source tree changes

        # TODO LORA

        # Update
        lsu = LSUMessage(self.componentinstancenumber, node_id, link_cost, self.clock)
        self.__update(lsu)

        if send_st:
            for link in self.source_trees[self.componentinstancenumber]:
                self.__add_message(STARMessageTypes.LSU, link)
                self.__broadcast_messages()

    def __on_lsu(self, k):
        pass

    def __update(self, lsu: LSUMessage):
        pass