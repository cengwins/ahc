#!/usr/bin/env python
"""
    Implementation of the Raymond's Algorithm for mutual exclusion.
"""

__author__ = "Berker Acır"
__contact__ = "berkeracir159@gmail.com"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Berker Acır"]
__date__ = "2021/05/18"
__deprecated__ = False
__email__ = "berkeracir159@gmail.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

from enum import Enum
from time import sleep
import networkx as nx

from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessagePayload, GenericMessageHeader, Topology


class RaymondEventTypes(Enum):
    TOKEN = "TOKEN"
    REQUEST = "REQUEST"
    PRIVILEGE = "PRIVILEGE"


class RaymondMessageTypes(Enum):
    TOKEN = "TOKEN"
    REQUEST = "REQUEST"


class RaymondMessageHeader(GenericMessageHeader):

    def __init__(self, messageType, messageFrom, messageTo, nextHop=float('inf'), interfaceID=float('inf'),
                 sequenceID=-1):
        super().__init__(messageType, messageFrom, messageTo, nextHop, interfaceID, sequenceID)


class RaymondMessagePayload(GenericMessagePayload):

    def __init__(self, nodeID):
        self.nodeID = nodeID


class MutualExclusionRaymondComponent(ComponentModel):
    privilegeSleepAmount = 1

    def __init__(self, componentName, componentID):
        super().__init__(componentName, componentID)

        self.eventhandlers[RaymondEventTypes.TOKEN] = self.token_received
        self.eventhandlers[RaymondEventTypes.REQUEST] = self.request_received
        self.eventhandlers[RaymondEventTypes.PRIVILEGE] = self.on_privilege

        self.neighborNodeIDs = set()
        self.parentNodeID = None
        self.queue = list()

        self.isRoot = False
        self.havePendingRequest = False
        self.isPrivileged = False

        self.privilegeCount = 0
        self.sentRequestCount = 0
        self.sentTokenCount = 0
        self.receivedRequestCount = 0
        self.receivedTokenCount = 0
        self.forwardedMessageCount = 0

    def on_init(self, eventobj: Event):
        mstG = nx.minimum_spanning_tree(Topology().G)
        self.neighborNodeIDs = set(mstG.neighbors(self.componentinstancenumber))
        if self.componentinstancenumber == 0:
            self.isRoot = True
        else:
            self.parentNodeID = nx.shortest_path(mstG, self.componentinstancenumber, 0)[1]

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        header = message.header
        messageType = header.messagetype
        messageTo = header.messageto

        if messageTo == self.componentinstancenumber:
            if messageType == RaymondMessageTypes.REQUEST:
                eventobj.event = RaymondEventTypes.REQUEST
                self.send_self(eventobj)
            elif messageType == RaymondMessageTypes.TOKEN:
                eventobj.event = RaymondEventTypes.TOKEN
                self.send_self(eventobj)

    def put(self, nodeID=None):
        if nodeID is None:
            nodeID = self.componentinstancenumber

        if not self.queue:
            headChanged = True
        else:
            headChanged = False
        self.queue.append(nodeID)
        if nodeID == self.componentinstancenumber:
            self.havePendingRequest = True

        if headChanged:
            if self.isRoot:
                if nodeID == self.componentinstancenumber:
                    self.send_self(Event(self, RaymondEventTypes.PRIVILEGE, None))
                else:
                    self.send_token(nodeID)
            else:
                self.send_request()

    def pop(self):
        nodeID = self.queue.pop(0)
        if nodeID == self.componentinstancenumber and nodeID not in self.queue:
            self.havePendingRequest = False

        if self.queue:
            head = self.queue[0]
            if self.isRoot:
                if head == self.componentinstancenumber:
                    self.send_self(Event(self, RaymondEventTypes.PRIVILEGE, None))
                else:
                    self.send_token(head)
            else:
                self.send_request()

    def on_privilege(self, eventobj: Event):
        self.isPrivileged = True

        self.privilegeCount += 1
        sleep(self.privilegeSleepAmount)

        self.isPrivileged = False
        self.pop()

    def token_received(self, eventobj: Event):
        self.receivedTokenCount += 1
        self.isRoot = True
        self.parentNodeID = None

        head = self.queue[0]
        if head == self.componentinstancenumber:
            self.send_self(Event(self, RaymondEventTypes.PRIVILEGE, None))
        else:
            self.send_token(head)

    def request_received(self, eventobj: Event):
        self.receivedRequestCount += 1
        receivedRequestNodeID = eventobj.eventcontent.payload.nodeID
        self.put(receivedRequestNodeID)

    def send_token(self, nodeID):
        self.sentTokenCount += 1
        self.isRoot = False
        self.parentNodeID = nodeID

        nextHop = self.parentNodeID
        interfaceID = f"{self.componentinstancenumber}-{nextHop}"
        header = RaymondMessageHeader(RaymondMessageTypes.TOKEN, self.componentinstancenumber, self.parentNodeID,
                                      nextHop, interfaceID)
        payload = RaymondMessagePayload(self.componentinstancenumber)
        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))

        self.pop()

    def send_request(self):
        self.sentRequestCount += 1
        nextHop = self.parentNodeID
        interfaceID = f"{self.componentinstancenumber}-{nextHop}"
        header = RaymondMessageHeader(RaymondMessageTypes.REQUEST, self.componentinstancenumber, self.parentNodeID,
                                      nextHop, interfaceID)
        payload = RaymondMessagePayload(self.componentinstancenumber)
        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))
