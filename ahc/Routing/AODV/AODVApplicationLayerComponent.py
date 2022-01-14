import os
import sys
import time
import random
from enum import Enum

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt
import threading

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
#from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from ahc.Routing.AODV.AODVNetworkLayerComponent import AODVNetworkLayerComponent
from ahc.Routing.AODV.AODVUtils import AODVMessageTypes, AODVMessageHeader

registry = ComponentRegistry()

class AODVApplicationLayerEventType(Enum):
      PROPOSE = "PROPOSE"

class AODVApplicationLayerComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_bottom(self, eventobj: Event):
        self.lock.acquire()
        
        msg = eventobj.eventcontent
        hdr = msg.header            
        #print(f"On MSFRB Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        if hdr.messagetype == AODVMessageTypes.RREP:
            self.send_self(Event(self,AODVApplicationLayerEventType.PROPOSE,eventobj.eventcontent))
        self.lock.release()

    def on_propose(self,eventobj:Event):
        self.lock.acquire()
        applmsg = eventobj.eventcontent
        applhdr = applmsg.header
        
        if applhdr.messagetype == AODVMessageTypes.RREP:
            print(f"Actual packet is ready to go from {self.componentname}.{self.componentinstancenumber} to {applhdr.messagefrom}")

            hdr = AODVMessageHeader(AODVMessageTypes.PROPOSE, self.componentinstancenumber,
                        applhdr.messagefrom,0,float('inf'),self.componentinstancenumber)
            data = self.MessageQueue[hdr.messageto]
            payload = GenericMessagePayload(data)
            message = GenericMessage(hdr, payload)
            #self.send_down(Event(self,EventTypes.MFRT,message))
        else:
            print(f"Wrong invocation of on_propose callback on {self.componentname}.{self.componentinstancenumber}")

        self.lock.release()

    #On-demand behavior sustained with this.
    def sendPackageToNode(self, destNodeID,msgFromUser):
        self.lock.acquire()
        #print(f"On sendPackageToNode {self.componentname}.{self.componentinstancenumber}")
        if self.componentinstancenumber == destNodeID:
            print(f"Node tries to sent itself so aborting")
            return
        hdr = AODVMessageHeader(AODVMessageTypes.PROPOSE, self.componentinstancenumber,
                                    destNodeID,0,float('inf'),self.componentinstancenumber)
        payload = GenericMessagePayload(msgFromUser)
        message = GenericMessage(hdr, payload)
        self.send_down(Event(self,EventTypes.MFRT,message))
        self.MessageQueue[destNodeID] = msgFromUser
        self.lock.release()

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.MessageQueue = {}
        self.lock = threading.Lock()
        self.eventhandlers[AODVApplicationLayerEventType.PROPOSE] = self.on_propose

