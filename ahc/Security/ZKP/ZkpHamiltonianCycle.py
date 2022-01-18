import numpy as np
import os
import sys
import random
import struct
import json
import networkx as nx
from ahc.Security.ZKP.PublicGraph import PublicGraph, PublicGraphHelper, FakeGraphHelper
from enum import Enum
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes, CipherContext
from Crypto.Random import get_random_bytes
from ahc.Ahc import \
    ComponentModel, Event, ConnectorTypes, ComponentRegistry, GenericMessagePayload, GenericMessageHeader, \
    GenericMessage, EventTypes
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

sys.path.insert(0, os.getcwd())
registry = ComponentRegistry()


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


class ProverType(Enum):
    HONEST = 0
    DISHONEST_FAKE_GRAPH = 1
    DISHONEST_FAKE_CYCLE = 2


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

    def print_received_message_info(self, message_header):
        print(
            f"Node-{self.componentinstancenumber} says "
            f"Node-{message_header.messagefrom} has sent {message_header.messagetype} message")

    def send_message(self, message_type, payload_data, destination):
        hdr = ApplicationLayerMessageHeader(message_type, self.componentinstancenumber, destination)
        payload = ApplicationLayerMessagePayload(payload_data)
        message = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))


class ProverApplicationLayerComponent(BaseZkpAppLayerComponent):
    def on_message_from_bottom(self, eventobj: Event):
        try:
            app_message = eventobj.eventcontent
            hdr = app_message.header
            """
            # uncomment to view message info
            self.print_received_message_info(hdr)
            """
            if hdr.messagetype == ApplicationLayerMessageTypes.CHALLENGE:
                self.send_self(Event(self, "challengereceived", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.CORRECT_RESPONSE:
                self.send_self(Event(self, "commit", app_message.payload.messagepayload))
            elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                self.print_end_result(message_type=hdr.messagetype)
                return
            elif hdr.messagetype == ApplicationLayerMessageTypes.REJECT:
                self.print_end_result(message_type=hdr.messagetype)
                return
        except AttributeError:
            print("Attribute Error")

    def on_commit(self, eventobj: Event):
        # (re)initialize nonces and encryptors
        self.create_nonces_and_encryptors()
        # permute graph and get node mapping
        public_graph = PublicGraph.get_graph()
        no_nodes = PublicGraph.get_graph_no_nodes()
        permuted_graph, self.graph["node_mapping"] = PublicGraphHelper.permute_graph(public_graph, no_nodes)
        # encrypt permuted graph
        self.graph["committed_graph"] = self.encrypt_graph(permuted_graph)
        # send encrypted and permuted graph to verifier
        self.send_message(ApplicationLayerMessageTypes.COMMIT,
                          PublicGraphHelper.convert_cypher_graph_to_bytes(self.graph["committed_graph"]),
                          self.destination)

    def on_fake_graph_commit(self, eventobj: Event):
        # (re)initialize nonces and encryptors
        self.create_nonces_and_encryptors()
        # permute graph and get node mapping
        fake_public_graph, self.secrets["hamiltonian_cycle"], _ = FakeGraphHelper.get_fake_public_graph()
        no_nodes = PublicGraph.get_graph_no_nodes()
        permuted_graph, self.graph["node_mapping"] = PublicGraphHelper.permute_graph(fake_public_graph, no_nodes)
        # encrypt permuted graph
        self.graph["committed_graph"] = self.encrypt_graph(permuted_graph)
        # send encrypted and permuted graph to verifier
        self.send_message(ApplicationLayerMessageTypes.COMMIT,
                          PublicGraphHelper.convert_cypher_graph_to_bytes(self.graph["committed_graph"]),
                          self.destination)

    def on_fake_cycle_commit(self, eventobj: Event):
        # (re)initialize nonces and encryptors
        self.create_nonces_and_encryptors()
        # permute graph and get node mapping
        public_graph, self.secrets["hamiltonian_cycle"], _ = FakeGraphHelper.get_public_graph_with_fake_cycle()
        no_nodes = PublicGraph.get_graph_no_nodes()
        permuted_graph, self.graph["node_mapping"] = PublicGraphHelper.permute_graph(public_graph, no_nodes)
        # encrypt permuted graph
        self.graph["committed_graph"] = self.encrypt_graph(permuted_graph)
        # send encrypted and permuted graph to verifier
        self.send_message(ApplicationLayerMessageTypes.COMMIT,
                          PublicGraphHelper.convert_cypher_graph_to_bytes(self.graph["committed_graph"]),
                          self.destination)

    def on_challenge_received(self, eventobj: Event):
        challenge_type = eventobj.eventcontent
        print(f"Received Challenge-{challenge_type}")
        if challenge_type == ChallengeType.PROVE_GRAPH:
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              self.create_prove_graph_payload(), self.destination)
        elif challenge_type == ChallengeType.SHOW_CYCLE:
            self.send_message(ApplicationLayerMessageTypes.RESPONSE,
                              self.create_show_cycle_payload(), self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def encrypt_graph(self, graph):
        permuted_matrix = nx.to_numpy_matrix(graph, nodelist=[*range(0, self.graph["graph_node_size"])])
        encrypted_matrix = np.asmatrix(np.zeros_like(permuted_matrix, dtype=CipherContext))
        for i in range(permuted_matrix.shape[0]):
            for j in range(permuted_matrix.shape[1]):
                cipher_text = self.crypto["encryptor"][i * permuted_matrix.shape[1] + j] \
                    .update(struct.pack('f', permuted_matrix[i, j]))
                encrypted_matrix[i, j] = cipher_text
        return encrypted_matrix

    def create_prove_graph_payload(self):
        payload = self.secrets["key"]
        for i in range(self.graph["graph_matrix_size"]):
            payload += self.secrets["nonces"][i]
        payload += json.dumps(self.graph["node_mapping"]).encode('utf-8')
        return payload

    def create_show_cycle_payload(self):
        cycle_nonces, index_list = self.get_cycle_nonces_indexes_as_bytes()
        payload = self.secrets["key"]
        payload += index_list
        payload += cycle_nonces
        return payload

    def get_cycle_nonces_indexes_as_bytes(self):
        hamiltonian_cycle = self.secrets["hamiltonian_cycle"]
        permuted_hamiltonian_cycle = nx.relabel_nodes(hamiltonian_cycle, self.graph["node_mapping"])
        cycle_nonces = b""
        index_list = b"{"
        for edge in list(permuted_hamiltonian_cycle.edges):
            cur_i = edge[0]
            cur_j = edge[1]
            # if part of the permuted hamiltonian cycle, add nonce with indexes
            cycle_nonces += self.secrets["nonces"][cur_i * self.graph["graph_node_size"] + cur_j]
            index_list += cur_i.to_bytes(2, "little") + cur_j.to_bytes(2, "little")
            # also add the symmetric edge
            cycle_nonces += self.secrets["nonces"][cur_j * self.graph["graph_node_size"] + cur_i]
            index_list += cur_j.to_bytes(2, "little") + cur_i.to_bytes(2, "little")
        index_list += b"}"
        return cycle_nonces, index_list

    def create_nonces_and_encryptors(self):
        if len(self.secrets["nonces"]) > 0 or len(self.crypto["encryptor"]) > 0:
            self.secrets["nonces"] = []
            self.crypto["encryptor"] = []
        for i in range(self.graph["graph_matrix_size"]):
            # add nonces for each
            self.secrets["nonces"].append(get_random_bytes(16))
            self.crypto["encryptor"].append(Cipher(algorithms.AES(self.secrets["key"]),
                                                   modes.CTR(self.secrets["nonces"][i]),
                                                   default_backend()).encryptor())

    def print_end_result(self, message_type: ApplicationLayerMessageTypes):
        if message_type == ApplicationLayerMessageTypes.ACCEPT:
            if self.type == ProverType.HONEST:
                print(f"ACCEPTED -> TRUE ACCEPT")
            else:
                print(f"ACCEPTED -> FALSE ACCEPT")
        elif message_type == ApplicationLayerMessageTypes.REJECT:
            if self.type == ProverType.HONEST:
                print(f"REJECTED -> FALSE REJECT")
            else:
                print(f"REJECTED -> TRUE REJECT")

    def __init__(self, componentname, componentinstancenumber, prover_type):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 1
        self.type = prover_type
        # graph related info for prover
        self.graph = {
            # encrypted and permuted new graph
            "committed_graph": np.asmatrix([]),
            "node_mapping": {},
            "graph_node_size": PublicGraph.get_graph_no_nodes(),
            "graph_matrix_size": PublicGraph.get_graph_matrix_size(),
            # This keyword is abstract, it is used to give intuition that prover knows the cycle
            "graph_auth_keyword": "BearsBeetsBattleStarGalactica",
        }
        # secrets of component
        self.secrets = {
            # key is 32 byte as AES use 256 bits key - updated at each commit
            "key": get_random_bytes(32),
            # nonce is 16 byte as AES use 128 bits block - updated at each commit
            "nonces": [],
            # hamiltonian cycle which is kept as a secret
            "hamiltonian_cycle": PublicGraph.get_hamiltonian_cycle(self.graph["graph_auth_keyword"])
        }
        # crypto tools
        self.crypto = {
            # AES has block size of 128 bits plain text block -> 128 bits cipher text block, holds list of encryptors
            "encryptor": []
        }
        self.eventhandlers["challengereceived"] = self.on_challenge_received
        self.eventhandlers["timerexpired"] = self.on_timer_expired
        # set on commit method according to prover type
        if prover_type == ProverType.HONEST:
            self.eventhandlers["commit"] = self.on_commit
        elif prover_type == ProverType.DISHONEST_FAKE_GRAPH:
            self.eventhandlers["commit"] = self.on_fake_graph_commit
        elif prover_type == ProverType.DISHONEST_FAKE_CYCLE:
            self.eventhandlers["commit"] = self.on_fake_cycle_commit


class VerifierApplicationLayerComponent(BaseZkpAppLayerComponent):
    def on_message_from_bottom(self, eventobj: Event):
        try:
            app_message = eventobj.eventcontent
            hdr = app_message.header
            """
            # uncomment to view message info
            self.print_received_message_info(hdr)
            """
            if hdr.messagetype == ApplicationLayerMessageTypes.COMMIT:
                """
                # uncomment to view the graph
                print(f"Received Commitment Graph:\n" 
                      f"{PublicGraphHelper.convert_bytes_to_cypher_graph(app_message.payload.messagepayload)}")
                """
                self.verification["committed_graph"] = \
                    PublicGraphHelper.convert_bytes_to_cypher_graph(app_message.payload.messagepayload)
                self.send_self(Event(self, "challenge", None))
            elif hdr.messagetype == ApplicationLayerMessageTypes.RESPONSE:
                self.send_self(Event(self, "responsereceived", app_message.payload.messagepayload))
        except AttributeError:
            print("Attribute Error")

    def on_challenge(self, eventobj: Event):
        if random.uniform(0, 1) < self.verification["probability"]:
            self.verification["current_challenge_mode"] = ChallengeType.PROVE_GRAPH
        else:
            self.verification["current_challenge_mode"] = ChallengeType.SHOW_CYCLE
        self.send_message(ApplicationLayerMessageTypes.CHALLENGE,
                          self.verification["current_challenge_mode"],
                          self.destination)

    def on_response_received(self, eventobj: Event):
        message_payload = eventobj.eventcontent
        if self.verification["current_challenge_mode"] == ChallengeType.PROVE_GRAPH:
            key, nonces, node_mapping = self.extract_prove_graph_response_payload(message_payload)
            if PublicGraphHelper.is_equal_to_public_graph(self.decrypt_graph(key, nonces), node_mapping):
                self.send_self(Event(self, "correctresponse", None))
            else:
                self.send_self(Event(self, "wrongresponse", None))
        elif self.verification["current_challenge_mode"] == ChallengeType.SHOW_CYCLE:
            key, nonces, index_list = self.extract_show_cycle_response_payload(message_payload)
            if PublicGraphHelper.graph_has_cycle(self.decrypt_graph(key, nonces, index_list)):
                self.send_self(Event(self, "correctresponse", None))
            else:
                self.send_self(Event(self, "wrongresponse", None))

    def on_correct_response(self, eventobj: Event):
        print(f"Correct Response Received")
        self.verification["current_trial_no"] += 1
        self.print_trial_info()
        if self.verification["current_trial_no"] == self.verification["max_trial_no"]:
            self.send_message(ApplicationLayerMessageTypes.ACCEPT, None, self.destination)
            return
        self.send_message(ApplicationLayerMessageTypes.CORRECT_RESPONSE, None, self.destination)

    def on_wrong_response(self, eventobj: Event):
        print("Wrong Response Received")
        self.send_message(ApplicationLayerMessageTypes.REJECT, None, self.destination)

    def on_timer_expired(self, eventobj: Event):
        pass

    def extract_prove_graph_response_payload(self, message_payload):
        key = message_payload[0:32]
        nonces = []
        for i in range(self.verification["graph_matrix_size"]):
            nonces.append(message_payload[i * 16 + 32: i * 16 + 48])
        node_mapping_json = json.loads(
            message_payload[self.verification["graph_matrix_size"] * 16 + 32:].decode('utf-8'))
        node_mapping = {}
        for k in node_mapping_json:
            node_mapping[int(k)] = node_mapping_json[k]
        return key, nonces, node_mapping

    def extract_show_cycle_response_payload(self, message_payload):
        key = message_payload[0:32]
        indices_start_index = message_payload[32:].find(b"{") + 1 + 32
        indices_end_index = message_payload[32:].find(b"}") + 32
        nonce_start_index = indices_end_index + 1
        index_list_bytes = message_payload[indices_start_index: indices_end_index]
        no_index = int((indices_end_index - indices_start_index) / 4)
        index_list = []
        nonces = []
        for i in range(no_index):
            current_i = int.from_bytes(index_list_bytes[i * 4: i * 4 + 2], "little")
            current_j = int.from_bytes(index_list_bytes[i * 4 + 2: i * 4 + 4], "little")
            index_list.append((current_i, current_j))
            nonces.append(message_payload[i * 16 + nonce_start_index: (i + 1) * 16 + nonce_start_index])
        return key, nonces, index_list

    def decrypt_graph(self, key, nonces, index_list=None):
        decrypted_matrix = np.asmatrix(np.zeros_like(self.verification["committed_graph"], dtype=float))
        if index_list is None:
            for i in range(decrypted_matrix.shape[0]):
                for j in range(decrypted_matrix.shape[1]):
                    decryptor = Cipher(algorithms.AES(key),
                                       modes.CTR(nonces[i * decrypted_matrix.shape[1] + j]),
                                       default_backend()).decryptor()
                    plain_text = struct.unpack('f', decryptor.update(self.verification["committed_graph"][i, j]))[0]
                    decrypted_matrix[i, j] = plain_text
        else:
            for i in range(len(index_list)):
                current_i, current_j = index_list[i]
                decryptor = Cipher(algorithms.AES(key),
                                   modes.CTR(nonces[i]),
                                   default_backend()).decryptor()
                plain_text = struct.unpack('f', decryptor.update(self.verification["committed_graph"]
                                                                 [current_i, current_j]))[0]
                decrypted_matrix[current_i, current_j] = plain_text
        """
        # uncomment to view the graph
        print("Received Decrypted Graph:\n", decrypted_matrix)
        """
        decrypted_graph = nx.from_numpy_matrix(decrypted_matrix)
        return decrypted_graph

    def print_trial_info(self):
        current_trial_no = self.verification["current_trial_no"]
        print(f"Trial No: {current_trial_no}\n"
              f"Probability for a Dishonest Prover: {0.5 ** current_trial_no}")

    def __init__(self, componentname, componentinstancenumber, max_trial_no, challenge_probability):
        super().__init__(componentname, componentinstancenumber)
        self.destination = 0
        # verification related data
        self.verification = {
            "current_trial_no": 0,
            "current_challenge_mode": ChallengeType.NONE,
            "max_trial_no": max_trial_no,
            "probability": challenge_probability,
            "committed_graph": np.asmatrix([]),
            "graph_matrix_size": PublicGraph.get_graph_matrix_size()
        }
        self.eventhandlers["challenge"] = self.on_challenge
        self.eventhandlers["responsereceived"] = self.on_response_received
        self.eventhandlers["correctresponse"] = self.on_correct_response
        self.eventhandlers["wrongresponse"] = self.on_wrong_response
        self.eventhandlers["timerexpired"] = self.on_timer_expired


class ProverAdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    # this function is used to set properties which are testable
    @staticmethod
    def set_properties(prover_type: ProverType):
        ProverAdHocNode.__PROVER_TYPE = prover_type

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = ProverApplicationLayerComponent("ProverApplicationLayer", componentid,
                                                         ProverAdHocNode.__PROVER_TYPE)
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

    __PROVER_TYPE = ProverType.HONEST


class VerifierAdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    # this function is used to set properties which are testable
    @staticmethod
    def set_properties(max_trial_no, challenge_probability):
        VerifierAdHocNode.__MAX_TRIAL_NO = max_trial_no
        VerifierAdHocNode.__CHALLENGE_PROBABILITY = challenge_probability

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = VerifierApplicationLayerComponent("VerifierApplicationLayer", componentid,
                                                           VerifierAdHocNode.__MAX_TRIAL_NO,
                                                           VerifierAdHocNode.__CHALLENGE_PROBABILITY)
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

    __MAX_TRIAL_NO = 10
    __CHALLENGE_PROBABILITY = 0.5
