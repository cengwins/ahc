import os
import queue
import sys
import time
import json
import queue
import random
import networkx as nx
from enum import Enum
import matplotlib.pyplot as plt
from datetime import datetime as dt

from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from Ahc import (ComponentModel, Event, ConnectorTypes, Topology,
                 ComponentRegistry, GenericMessagePayload, GenericMessageHeader,
                 GenericMessage, EventTypes)

registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageType(Enum):
    BASIC = "basic"
    CONTROL = "control"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass

class ApplicationLayerComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber, context):
        super().__init__(componentname, componentinstancenumber, context=context)

        self.context = context
        # self.eventhandlers[ApplicationLayerMessageType.BASIC] = self.on_basic_message
        # self.eventhandlers[ApplicationLayerMessageType.CONTROL] = self.on_control_message

        self.basic_message_queue = queue.Queue(maxsize=-1)
        self.control_message_queue = queue.Queue(maxsize=-1)

    def prepare_application_layer_message(self, message_type: ApplicationLayerMessageType, destination_node_id: int, payload: object) -> GenericMessage:
        hdr = ApplicationLayerMessageHeader(message_type, self.componentinstancenumber, destination_node_id)
        payload = ApplicationLayerMessagePayload(payload)
        
        return GenericMessage(hdr, payload)

    def send_random_basic_message(self, to: int) -> None:
        self.send_down(Event(self, EventTypes.MFRT, self.prepare_application_layer_message(ApplicationLayerMessageType.BASIC, to, str(dt.now().timestamp()))))

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        if self.componentinstancenumber == 0:
            self.send_random_basic_message(3)

    def on_message_from_bottom(self, eventobj: Event):
        applmessage = eventobj.eventcontent
        hdr = applmessage.header

        print(f"Node-{self.componentinstancenumber}: Node-{hdr.messagefrom} has sent {hdr.messagetype} message (payload: {applmessage.payload})")

        if hdr.messagetype == ApplicationLayerMessageType.BASIC:
            self.basic_message_queue.put_nowait(applmessage)
        elif hdr.messagetype == ApplicationLayerMessageType.CONTROL:
            self.control_message_queue.put_nowait(applmessage)

class AdHocNode(ComponentModel):
    def __init__(self, componentname, componentid, context):
        self.context = context
        # SUBCOMPONENTS
        self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid, context=self.context)
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

        super().__init__(componentname, componentid, context=self.context)

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))