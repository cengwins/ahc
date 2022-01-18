import os
import sys
import random
import time
from enum import Enum

import networkx as nx

sys.path.insert(0,os.getcwd())

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, ComponentRegistry
from ahc.Ahc import GenericMessageHeader, GenericMessagePayload, GenericMessage
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

registry = ComponentRegistry()

def generate_random_graph(node_count, edge_creation_probability):
    random_graph = nx.gnp_random_graph(node_count, edge_creation_probability)
    return random_graph

def generate_random_permutation(graph, permutations_set):
    permutation = dict(zip(graph.nodes(), sorted(graph.nodes(), key=lambda k: random.random())))
    while permutation in permutations_set:
        permutation = dict(zip(graph.nodes(), sorted(graph.nodes(), key=lambda k: random.random())))

    permutations_set.append(permutation)
    return permutation

def generate_isomorphic_graph(graph, permutation):
    return nx.relabel_nodes(graph,permutation)

def graphs_are_equal(graph1, graph2):
    if graph1.adj == graph2.adj:
        return True
    return False

def inverse_permutation(permutation):
    return dict((v, k) for k, v in permutation.items())

def permutation_of_permutation(permutation1, permutation2):
    res = {key: permutation2.get(permutation1.get(key))
           for key in permutation1.keys()}
    return res


#region global variables

# timestmp_beginning = 0
number_of_trials = 10
number_of_nodes = 200
edge_creation_probability = 0.5
G1 = generate_random_graph(number_of_nodes, edge_creation_probability)
permutations_set = [dict(zip(G1.nodes(), sorted(G1.nodes())))]
secret_key = generate_random_permutation(G1, permutations_set)
G2 = generate_isomorphic_graph(G1, secret_key)

public_key = G1, G2

#endregion

class ApplicationLayerMessageTypes(Enum):
    GRAPH = "GRAPH"
    GRAPHREQUEST = "GRAPHREQUEST"
    PROVE = "PROVE"
    PERMUTATION = "PERMUTATION"

class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass

class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass

class ApplicationLayerPeggy(ComponentModel):
    public_key = public_key
    secret_key = secret_key
    permutations_set = permutations_set

    def on_init(self, eventobj: Event):
        # global timestmp_beginning
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        # timestmp_beginning = time.time()
        print("Trials beginning!")

        self.destination = 1
        self.random_permutation = generate_random_permutation(self.public_key[0], self.permutations_set)
        self.random_graph = generate_isomorphic_graph(self.public_key[0], self.random_permutation)

        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.GRAPH, self.componentinstancenumber,
                                            self.destination)
        payload = ApplicationLayerMessagePayload(self.random_graph)
        message = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))

    def on_message_from_bottom(self, eventobj: Event):
        global trial_count
        applmessage = eventobj.eventcontent
        hdr = applmessage.header

        if hdr.messagetype == ApplicationLayerMessageTypes.PROVE:
            if applmessage.payload.messagepayload == "G1":
                permutation = inverse_permutation(self.random_permutation)
                hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PERMUTATION, self.componentinstancenumber,
                                                    self.destination)

                payload = ApplicationLayerMessagePayload(permutation)
                message = GenericMessage(hdr, payload)
                self.send_down(Event(self, EventTypes.MFRT, message))

            elif applmessage.payload.messagepayload == "G2":
                permutation = permutation_of_permutation(inverse_permutation(self.random_permutation), self.secret_key)
                hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PERMUTATION, self.componentinstancenumber,
                                                    self.destination)

                payload = ApplicationLayerMessagePayload(permutation)
                message = GenericMessage(hdr, payload)
                self.send_down(Event(self, EventTypes.MFRT, message))

        elif hdr.messagetype == ApplicationLayerMessageTypes.GRAPHREQUEST:
            self.random_permutation = generate_random_permutation(self.public_key[0], self.permutations_set)
            self.random_graph = generate_isomorphic_graph(self.public_key[0], self.random_permutation)
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.GRAPH, self.componentinstancenumber,
                                                self.destination)

            payload = ApplicationLayerMessagePayload(self.random_graph)
            message = GenericMessage(hdr, payload)
            self.send_down(Event(self, EventTypes.MFRT, message))

class ApplicationLayerVictor(ComponentModel):
    public_key = public_key

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        self.received_random_graph = None
        self.received_permutation = None
        self.choice = 0
        self.trial_count = 0
        self.finished = False
        self.destination = 0

    def on_message_from_bottom(self, eventobj: Event):
        global number_of_trials #, timestmp_beginning
        applmessage = eventobj.eventcontent
        hdr = applmessage.header

        if hdr.messagetype == ApplicationLayerMessageTypes.GRAPH:
            self.received_random_graph = applmessage.payload.messagepayload
            self.choice = random.choice([0, 1])

            if self.choice == 0:
                hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROVE, self.componentinstancenumber,
                                                    self.destination)
                payload = ApplicationLayerMessagePayload("G1")
                message = GenericMessage(hdr, payload)
                self.send_down(Event(self, EventTypes.MFRT, message))
            elif self.choice == 1:
                hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROVE, self.componentinstancenumber,
                                                        self.destination)
                payload = ApplicationLayerMessagePayload("G2")
                message = GenericMessage(hdr, payload)
                self.send_down(Event(self, EventTypes.MFRT, message))
        elif hdr.messagetype == ApplicationLayerMessageTypes.PERMUTATION:
            self.received_permutation = applmessage.payload.messagepayload
            generated_graph = generate_isomorphic_graph(self.received_random_graph, self.received_permutation)
            if self.choice == 0:
                if graphs_are_equal(generated_graph, self.public_key[0]):
                    print("Trial: " + str(self.trial_count + 1) + " passed! Checked with G1!")
                    self.trial_count += 1
                    if self.trial_count == number_of_trials:
                        self.finished = True
                else:
                    print("Trial: " + str(self.trial_count+1) + " failed!")
                    self.finished = True
            elif self.choice == 1:
                if graphs_are_equal(generated_graph, self.public_key[1]):
                    print("Trial: " + str(self.trial_count+1) + " passed! Checked with G2!")
                    self.trial_count += 1
                    if self.trial_count == number_of_trials:
                        self.finished = True
                else:
                    print("Trial: " + str(self.trial_count+1) + " failed!")
                    self.finished = True

            if not self.finished:
                hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.GRAPHREQUEST,
                                                    self.componentinstancenumber,
                                                    self.destination)
                message = GenericMessage(hdr, None)
                self.send_down(Event(self, EventTypes.MFRT, message))
            else:
                print("Trials completed!")
                # timestmp_end = time.time()
                # print(timestmp_end - timestmp_beginning)

class NodePeggy(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)

        self.applicationlayer = ApplicationLayerPeggy("ApplicationLayer", componentid)
        self.networklayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)

        self.applicationlayer.connect_me_to_component(ConnectorTypes.DOWN, self.networklayer)
        self.networklayer.connect_me_to_component(ConnectorTypes.UP, self.applicationlayer)
        self.networklayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.networklayer)

        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

class NodeVictor(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)

        self.applicationlayer = ApplicationLayerVictor("ApplicationLayer", componentid)
        self.networklayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)

        self.applicationlayer.connect_me_to_component(ConnectorTypes.DOWN, self.networklayer)
        self.networklayer.connect_me_to_component(ConnectorTypes.UP, self.applicationlayer)
        self.networklayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.networklayer)

        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
