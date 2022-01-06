import numpy as np
import os
import sys
import time
import random
import networkx as nx
from enum import Enum
from Ahc import ComponentModel, Event, ConnectorTypes, ComponentRegistry, GenericMessagePayload, GenericMessageHeader, \
    GenericMessage, EventTypes
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from typing import Final

sys.path.insert(0, os.getcwd())
registry = ComponentRegistry()


class PublicGraph:
    def __generate_graph_with_hamiltonian_cycle(self):
        public_graph = nx.Graph()
        public_graph.add_nodes_from(range(0, 5))
        for i in range(4):
            public_graph.add_edge(i, i + 1, attr=True)
        public_graph.add_edge(4, 0, attr=True)
        print(nx.to_numpy_matrix(public_graph, nodelist=[*range(0, 5)]))
        return public_graph

    @staticmethod
    def get_graph():
        return PublicGraph.__GRAPH

    @staticmethod
    def convert_graph_to_string(graph):
        return nx.to_numpy_matrix(graph, nodelist=[*range(0, 5)]).tostring()

    __GRAPH: Final = __generate_graph_with_hamiltonian_cycle(self=None)


# define your own message types
class ApplicationLayerMessageTypes(Enum):
    COMMIT = "COMMIT"
    CHALLENGE = "CHALLENGE"
    RESPONSE = "RESPONSE"
    CORRECT_RESPONSE = "CORRECT_RESPONSE"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class ChallengeType(Enum):
    PROVE_GRAPH = 0
    SHOW_CYCLE = 1


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


class BaseZkpAppLayerComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        if self.componentinstancenumber == 0:
            print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
            self.send_self(Event(self, "commit", None))
        else:
            pass

    def send_message(self, message_type, payload_data, destination):
        hdr = ApplicationLayerMessageHeader(message_type, self.componentinstancenumber, destination)
        payload = ApplicationLayerMessagePayload(payload_data)
        message = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))


class PeggyApplicationLayerComponent(BaseZkpAppLayerComponent):
    def on_message_from_bottom(self, eventobj: Event):
        try:
            app_message = eventobj.eventcontent
            hdr = app_message.header
            if hdr.messagetype == ApplicationLayerMessageTypes.CHALLENGE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                print(f"Challenge-{app_message.payload.messagepayload}")
                self.send_self(Event(self, "challengereceived", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.CORRECT_RESPONSE:
                self.send_self(Event(self, "commit", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
            elif hdr.messagetype == ApplicationLayerMessageTypes.REJECT:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        except AttributeError:
            print("Attribute Error")

    def on_commit(self, eventobj: Event):
        self.new_graph = self.permute_graph()
        print("Permuted\n", nx.to_numpy_matrix(self.new_graph, nodelist=[*range(0, 5)]))
        self.send_message(ApplicationLayerMessageTypes.COMMIT, PublicGraph.convert_graph_to_string(self.new_graph),
                          self.destination)

    def on_challenge_received(self, eventobj: Event):
        challenge_type = eventobj.eventcontent
        if challenge_type == ChallengeType.PROVE_GRAPH:
            print("Recieved", challenge_type)
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              PublicGraph.convert_graph_to_string(self.new_graph), self.destination)
        elif challenge_type == ChallengeType.SHOW_CYCLE:
            print("Recieved", challenge_type)
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              PublicGraph.convert_graph_to_string(self.new_graph), self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def permute_graph(self):
        public_graph = PublicGraph.get_graph()
        nodes = [*range(0, 5)]
        shuffled_nodes = random.sample(nodes, len(nodes))
        node_mapping = {}
        for i in range(5):
            node_mapping[i] = shuffled_nodes[i]
        return nx.relabel_nodes(public_graph, node_mapping)

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 1
        self.new_graph = None
        self.eventhandlers["commit"] = self.on_commit
        self.eventhandlers["challengereceived"] = self.on_challenge_received
        self.eventhandlers["timerexpired"] = self.on_timer_expired


class VictorApplicationLayerComponent(BaseZkpAppLayerComponent):
    MAX_TRIAL: Final = 10

    def on_message_from_bottom(self, eventobj: Event):
        try:
            app_message = eventobj.eventcontent
            hdr = app_message.header
            if hdr.messagetype == ApplicationLayerMessageTypes.COMMIT:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                print(f"Graph-\n{np.fromstring(app_message.payload.messagepayload, dtype=float).reshape(5, 5)}")
                self.send_self(Event(self, "challenge", None))
            elif hdr.messagetype == ApplicationLayerMessageTypes.RESPONSE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                self.send_self(Event(self, "responsereceived", app_message.payload.messagepayload))
        except AttributeError:
            print("Attribute Error")

    def on_challenge(self, eventobj: Event):
        self.send_message(ApplicationLayerMessageTypes.CHALLENGE, ChallengeType.PROVE_GRAPH, self.destination)

    def on_response_received(self, eventobj: Event):
        self.send_self(Event(self, "correctresponse", None))
        pass

    def on_correct_response(self, eventobj: Event):
        self.trial += 1
        if self.trial == self.MAX_TRIAL:
            self.send_message(ApplicationLayerMessageTypes.ACCEPT, None, self.destination)
            return
        self.send_message(ApplicationLayerMessageTypes.CORRECT_RESPONSE, None, self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 0
        self.trial = 0
        self.eventhandlers["challenge"] = self.on_challenge
        self.eventhandlers["responsereceived"] = self.on_response_received
        self.eventhandlers["correctresponse"] = self.on_correct_response
        self.eventhandlers["timerexpired"] = self.on_timer_expired


class PeggyAdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = PeggyApplicationLayerComponent("PeggyApplicationLayer", componentid)
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


class VictorAdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = VictorApplicationLayerComponent("VictorApplicationLayer", componentid)
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
