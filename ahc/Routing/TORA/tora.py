import time
from enum import Enum
from threading import Lock
from typing import Dict, List, Tuple

from ahc.Ahc import (
    ComponentModel,
    ConnectorTypes,
    Event,
    EventTypes,
    GenericMessage,
    GenericMessageHeader,
    GenericMessagePayload,
    Topology,
)
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

INITIAL_TIME = 20000000000
benchmark_time_lock: Lock = Lock()
benchmark_time: float = 20000000000


class ApplicationLayerMessageTypes(Enum):
    UPD = "UPDATE"
    CLR = "CLEAR"
    QRY = "QUERY"
    MSG = "MESSAGE"


class TORAHeight:
    def __init__(self, tau: float, oid: int, r: int, delta: int, i: int):
        self.tau = tau
        self.oid = oid
        self.r = r
        self.delta = delta
        self.i = i


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


class ApplicationLayerQueryMessagePayload(GenericMessagePayload):
    did: int

    def __init__(self, did: int):
        self.did = did


class ApplicationLayerClearMessagePayload(GenericMessagePayload):
    did: int
    reference: Tuple[int, int, int]

    def __init__(self, did: int, reference: Tuple[int, int, int]):
        self.did = did
        self.reference = reference


class ApplicationLayerUpdateMessagePayload(GenericMessagePayload):
    did: int
    height: TORAHeight
    link_reversal: bool

    def __init__(self, did: int, height: TORAHeight, link_reversal: bool):
        self.did = did
        self.height = height
        self.link_reversal = link_reversal


class ApplicationLayerMessageMessagePayload(GenericMessagePayload):
    did: int
    message: str

    def __init__(self, did: int, message: str):
        self.did = did
        self.message = message


class RoutingTORAApplicationLayerComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.neighbors = Topology().get_neighbors(componentinstancenumber)

        self.height: TORAHeight = TORAHeight(
            None, None, None, None, self.componentinstancenumber
        )

        self.last_upd: int = 0
        self.rr: bool = 0
        self.N: Dict[int, Tuple[TORAHeight, int]] = {}
        self.lock: Lock = Lock()

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        self.update_time()
        with self.lock:
            try:
                applmessage = eventobj.eventcontent
                hdr = applmessage.header
                payload: GenericMessagePayload = applmessage.payload
                if hdr.messagetype == ApplicationLayerMessageTypes.QRY:
                    self.handle_qry(payload.did, hdr.messagefrom)
                elif hdr.messagetype == ApplicationLayerMessageTypes.UPD:
                    self.handle_upd(
                        payload.did,
                        hdr.messagefrom,
                        payload.height,
                        payload.link_reversal,
                    )
                elif hdr.messagetype == ApplicationLayerMessageTypes.CLR:
                    self.handle_clr(payload.did, payload.reference)
                elif hdr.messagetype == ApplicationLayerMessageTypes.MSG:
                    self.handle_msg(payload.did, payload.message)
            except AttributeError:
                print("Attribute Error")
        self.update_time()

    def handle_qry(self, did: int, fromid: int):
        downstream_links = self.get_downstream_links()

        if len(downstream_links) == 0:
            if self.rr == 0:
                self.broadcast_qry(did)
            else:
                pass
        elif self.height.delta is None:
            min_height = self.get_minimum_height_between_neighbours()
            self.height = TORAHeight(
                min_height.tau,
                min_height.oid,
                min_height.r,
                min_height.delta + 1,
                self.componentinstancenumber,
            )
            self.broadcast_upd(did, False)
        elif fromid not in self.N or (
            fromid in self.N and self.N[fromid][1] > self.last_upd
        ):
            self.broadcast_upd(did, False)
        else:
            pass

    def handle_upd(
        self, did: int, from_id: int, height: TORAHeight, link_reversal: bool
    ):
        self.set_neighbour_height(from_id, height)
        downstream_links = self.get_downstream_links()

        if link_reversal:
            
            if len(downstream_links):
                return

            upstream_links: List[Tuple[TORAHeight, int]] = list(
                self.get_upstream_links().items()
            )
            reference_level: TORAHeight = TORAHeight(-1, None, None, None, None)
            same_reference_level = True

            for t in upstream_links:
                upstream_link = t[0]
                if reference_level == (-1, None, None):
                    reference_level = upstream_link
                elif (
                    upstream_link.tau != reference_level.tau
                    or upstream_link.oid != reference_level.oid
                    or upstream_link.r != reference_level.r
                ):
                    same_reference_level = False

                if (reference_level.tau, reference_level.oid, reference_level.r) >= (
                    upstream_link.tau,
                    upstream_link.oid,
                    upstream_link.r,
                ):
                    reference_level.tau = upstream_link.tau
                    reference_level.oid = upstream_link.oid
                    reference_level.r = upstream_link.r
                    reference_level.delta = min(
                        reference_level.delta, upstream_link.delta
                    )

            if not same_reference_level:
                self.maintenance_case_2(did, reference_level)
            elif reference_level[2] == 0:
                self.maintenance_case_3(did, reference_level)
            elif self.componentinstancenumber == reference_level[1]:
                self.maintenance_case_4(did)
            else:
                self.maintenance_case_5(did)
        else:
            if self.rr == 1:
                min_height = self.get_minimum_height_between_neighbours()
                self.height = TORAHeight(
                    min_height.tau,
                    min_height.oid,
                    min_height.r,
                    min_height.delta + 1,
                    self.componentinstancenumber,
                )
                self.rr = 0
                self.broadcast_upd(did, False)
            else:
                if len(downstream_links) == 0 and self.componentinstancenumber != did:
                    self.maintenance_case_1(did)

    def handle_clr(self, did: int, reference: Tuple[int, int, int]):
        if reference == (self.height.tau, self.height.oid, self.height.r):
            self.height = TORAHeight(
                None, None, None, None, self.componentinstancenumber
            )

        for neighbour in self.N:
            if neighbour == did:
                continue
            if reference == (
                self.height.tau,
                self.height.oid,
                self.height.r,
            ) or reference == (
                self.N[neighbour][0].tau,
                self.N[neighbour][0].oid,
                self.N[neighbour][0].r,
            ):
                self.N[neighbour] = (
                    None,
                    None,
                    None,
                    None,
                    self.componentinstancenumber,
                )
        if reference == (self.height.tau, self.height.oid, self.height.r):
            self.broadcast_clr(did, reference)

    def handle_msg(self, did: int, message: str):
        if did == self.componentinstancenumber:
            print(f"{self.componentinstancenumber} says: Got a message: {message}")
        elif len(self.get_downstream_links()) == 0:
            print(
                f"{self.componentinstancenumber} says: Sorry I can't route this message :("
            )
        else:
            min_neighbour = self.get_minimum_height_between_neighbours()
            print(
                f"{self.componentinstancenumber} says: Forwarding a message: {message}"
            )
            hdr = ApplicationLayerMessageHeader(
                ApplicationLayerMessageTypes.MSG,
                self.componentinstancenumber,
                min_neighbour.i,
            )
            msg = GenericMessage(
                hdr, ApplicationLayerMessageMessagePayload(did, message)
            )
            self.send_down(Event(self, EventTypes.MFRT, msg))

    def maintenance_case_1(self, did: int):
        upstream_links = self.get_upstream_links()

        if len(upstream_links) == 0:
            self.height = TORAHeight(
                None, None, None, None, self.componentinstancenumber
            )
        else:
            self.height = TORAHeight(
                time.time(),
                self.componentinstancenumber,
                0,
                0,
                self.componentinstancenumber,
            )

        self.broadcast_upd(did, True)

    def maintenance_case_2(self, did: int, reference: TORAHeight):
        self.height = TORAHeight(
            reference.tau,
            reference.oid,
            reference.r,
            reference.delta - 1,
            self.componentinstancenumber,
        )
        self.broadcast_upd(did, True)

    def maintenance_case_3(self, did: int, reference: TORAHeight):
        self.height = TORAHeight(
            reference.tau, reference.oid, 1, 0, self.componentinstancenumber
        )
        self.broadcast_upd(did, True)

    def maintenance_case_4(self, did: int):
        self.height = TORAHeight(None, None, None, None, self.componentinstancenumber)

        for neighbour in self.N:
            if neighbour == did:
                continue
            self.N[neighbour] = (
                None,
                None,
                None,
                None,
                self.componentinstancenumber,
            )

        self.broadcast_clr(did, (self.height.tau, self.height.oid, 1))

    def maintenance_case_5(self, did: int):
        self.height = TORAHeight(
            time.time(),
            self.componentinstancenumber,
            0,
            0,
            self.componentinstancenumber,
        )
        self.broadcast_upd(did, True)

    def get_minimum_height_between_neighbours(self) -> TORAHeight:
        downstream_links = self.get_downstream_links()
        min_height = downstream_links[list(downstream_links)[0]][0]
        min_height_delta = min_height.delta

        for i in list(downstream_links):
            downstream_link = downstream_links[i]

            if min_height_delta > downstream_link[0].delta + 1:
                min_height = downstream_link[0]
                min_height_delta = downstream_link[0].delta + 1

        return min_height

    def get_downstream_links(self):
        height_delta = 100000 if self.height.delta is None else self.height.delta
        return dict(
            filter(lambda link: link[1][0].delta < height_delta, list(self.N.items()))
        )

    def get_upstream_links(self):
        height_delta = -1 if self.height.delta is None else self.height.delta
        return dict(
            filter(lambda link: link[1][0].delta >= height_delta, list(self.N.items()))
        )

    def broadcast_qry(self, did: int):
        self.rr = 1
        self.broadcast(
            ApplicationLayerQueryMessagePayload(did), ApplicationLayerMessageTypes.QRY
        )

    def broadcast_upd(self, did: int, link_reversal: bool):
        self.last_upd = time.time()
        self.broadcast(
            ApplicationLayerUpdateMessagePayload(did, self.height, link_reversal),
            ApplicationLayerMessageTypes.UPD,
        )

    def broadcast_clr(self, did: int, reference: Tuple[int, int, int]):
        self.broadcast(
            ApplicationLayerClearMessagePayload(did, reference),
            ApplicationLayerMessageTypes.CLR,
        )

    def broadcast(
        self, payload: GenericMessagePayload, t: ApplicationLayerMessageTypes
    ):
        print(f"Node-{self.componentinstancenumber} is broadcasting a {t} message")
        for destination in self.neighbors:
            hdr = ApplicationLayerMessageHeader(
                t,
                self.componentinstancenumber,
                destination,
            )
            msg = GenericMessage(hdr, payload)
            self.send_down(Event(self, EventTypes.MFRT, msg))

    def set_height(self, height: TORAHeight):
        self.height = height

        for destination_neighbour in self.neighbors:
            Topology().nodes[destination_neighbour].set_neighbour_height(
                self.componentinstancenumber, height
            )

    def set_neighbour_height(self, j: int, height: TORAHeight):
        self.N[j] = (height, time.time())

    def update_time(self):
        global benchmark_time
        with benchmark_time_lock:
            if benchmark_time < time.time() or benchmark_time == INITIAL_TIME:
                benchmark_time = time.time()


class RoutingTORAComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = RoutingTORAApplicationLayerComponent(
            "ApplicationLayer", componentid
        )
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

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def init_route_creation(self, did: int):
        self.appllayer.handle_qry(did, self.componentinstancenumber)

    def set_height(self, height: TORAHeight):
        self.appllayer.set_height(height)

    def send_message(self, did: int, message: str):
        self.appllayer.handle_msg(did, message)

    def set_neighbour_height(self, j: int, height: TORAHeight):
        self.appllayer.set_neighbour_height(j, height)


### Functions to get variables stored in nodes.
### Used in visiualization.


def all_edges(topo: Topology):
    edges = []
    for node in topo.nodes:
        downstream_links = topo.nodes[node].appllayer.get_downstream_links()

        for i in list(downstream_links):
            edges.append((node, i))

    return edges


def heights(topo: Topology):
    heights = []
    for node in topo.nodes:
        heights.append((node, topo.nodes[node].appllayer.height.delta))
    return heights


### Functions used in benchmark


def wait_for_action_to_complete():
    while time.time() - 0.25 < benchmark_time:
        time.sleep(0.25)
    return benchmark_time


def set_benchmark_time():
    global benchmark_time
    benchmark_time = INITIAL_TIME
