import numpy as np
import os
import sys
import random
import struct
import networkx as nx
from enum import Enum
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes, CipherContext
from Crypto.Random import get_random_bytes
from typing import Final
from Ahc import \
    ComponentModel, Event, ConnectorTypes, ComponentRegistry, GenericMessagePayload, GenericMessageHeader, \
    GenericMessage, EventTypes
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

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
    def convert_cypher_graph_to_string(graph):
        graph_bytes = b""
        for i in range(graph.shape[0]):
            for j in range(graph.shape[1]):
                graph_bytes += graph[i, j]
        print("Str graph", graph_bytes)
        return graph_bytes

    @staticmethod
    def convert_string_to_cypher_graph(graph_bytes):
        matrix = np.asmatrix(np.zeros((5, 5), dtype=CipherContext))
        tmp_graph_bytes = graph_bytes
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                tmp_edge_bytes = tmp_graph_bytes[0:4]
                tmp_graph_bytes = tmp_graph_bytes[4:]
                matrix[i, j] = tmp_edge_bytes
        print("Graph Redesigned\n", matrix)
        return matrix

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
    NONE = -1
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
                    f"Node-{self.componentinstancenumber} says"
                    f"Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                print(f"Challenge-{app_message.payload.messagepayload}")
                self.send_self(Event(self, "challengereceived", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.CORRECT_RESPONSE:
                self.send_self(Event(self, "commit", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                print(
                    f"Node-{self.componentinstancenumber} says"
                    f"Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
            elif hdr.messagetype == ApplicationLayerMessageTypes.REJECT:
                print(
                    f"Node-{self.componentinstancenumber} says "
                    f"Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        except AttributeError:
            print("Attribute Error")

    def on_commit(self, eventobj: Event):
        # permute graph and get node mapping
        permuted_graph, self.graph["node_mapping"] = self.permute_graph()
        # encrypt permuted graph
        self.graph["new_graph"] = self.encrypt_graph(permuted_graph)
        # send encrypted and permuted graph to verifier
        self.send_message(ApplicationLayerMessageTypes.COMMIT,
                          PublicGraph.convert_cypher_graph_to_string(self.graph["new_graph"]),
                          self.destination)

    def on_challenge_received(self, eventobj: Event):
        challenge_type = eventobj.eventcontent
        if challenge_type == ChallengeType.PROVE_GRAPH:
            print("Recieved", challenge_type)
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              PublicGraph.convert_cypher_graph_to_string(self.graph["new_graph"]), self.destination)
        elif challenge_type == ChallengeType.SHOW_CYCLE:
            print("Recieved", challenge_type)
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              PublicGraph.convert_cypher_graph_to_string(self.graph["new_graph"]), self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def permute_graph(self):
        # get public graph
        public_graph = PublicGraph.get_graph()
        nodes = [*range(0, 5)]
        shuffled_nodes = random.sample(nodes, len(nodes))
        node_mapping = {}
        # form node mapping
        for i in range(5):
            node_mapping[i] = shuffled_nodes[i]
        # return permuted graph with node mapping
        return nx.relabel_nodes(public_graph, node_mapping), node_mapping

    def encrypt_graph(self, graph):
        matrix = nx.to_numpy_matrix(graph, nodelist=[*range(0, 5)])
        encrypted_matrix = np.asmatrix(np.zeros_like(matrix, dtype=CipherContext))
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                cipher_text = self.crypto["encryptor"].update(struct.pack('f', matrix[i, j]))
                encrypted_matrix[i, j] = cipher_text
        return encrypted_matrix

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 1
        # graph related info for prover
        self.graph = {
            # encrypted and permuted new graph
            "new_graph": np.asmatrix([]),
            "node_mapping": {}
        }
        # secrets of component
        self.secrets = {
            # key is 32 byte as AES use 256 bits
            "key": get_random_bytes(32),
            # IV is 16 byte as AES use block size 128 bits
            "iv": get_random_bytes(16)
        }
        # crypto tools
        self.crypto = {
            # AES has block size of 128 bits plain text block -> 128 bits cipher text block
            "encryptor": Cipher(algorithms.AES(self.secrets["key"]), modes.CFB(self.secrets["iv"]),
                                default_backend()).encryptor(),
            "decryptor": Cipher(algorithms.AES(self.secrets["key"]), modes.CFB(self.secrets["iv"]),
                                default_backend()).decryptor()
        }
        self.eventhandlers["commit"] = self.on_commit
        self.eventhandlers["challengereceived"] = self.on_challenge_received
        self.eventhandlers["timerexpired"] = self.on_timer_expired


class VictorApplicationLayerComponent(BaseZkpAppLayerComponent):
    def on_message_from_bottom(self, eventobj: Event):
        try:
            app_message = eventobj.eventcontent
            hdr = app_message.header
            if hdr.messagetype == ApplicationLayerMessageTypes.COMMIT:
                print(
                    f"Node-{self.componentinstancenumber} says "
                    f"Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                print(f"Graph-\n{PublicGraph.convert_string_to_cypher_graph(app_message.payload.messagepayload)}")
                self.send_self(Event(self, "challenge", None))
            elif hdr.messagetype == ApplicationLayerMessageTypes.RESPONSE:
                print(
                    f"Node-{self.componentinstancenumber} says "
                    f"Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
                self.send_self(Event(self, "responsereceived", app_message.payload.messagepayload))
        except AttributeError:
            print("Attribute Error")

    def on_challenge(self, eventobj: Event):
        self.send_message(ApplicationLayerMessageTypes.CHALLENGE, ChallengeType.PROVE_GRAPH, self.destination)

    def on_response_received(self, eventobj: Event):
        self.send_self(Event(self, "correctresponse", None))
        pass

    def on_correct_response(self, eventobj: Event):
        self.verification["current_trial_no"] += 1
        if self.verification["current_trial_no"] == self.verification["max_trial_no"]:
            self.send_message(ApplicationLayerMessageTypes.ACCEPT, None, self.destination)
            return
        self.send_message(ApplicationLayerMessageTypes.CORRECT_RESPONSE, None, self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 0
        # verification related data
        self.verification = {
            "current_trial_no": 0,
            "current_challenge_mode": ChallengeType.NONE,
            "max_trial_no": 1
        }
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

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
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

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

        super().__init__(componentname, componentid)
