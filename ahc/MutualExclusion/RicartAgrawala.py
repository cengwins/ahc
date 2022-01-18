#!/usr/bin/env python
"""
    Implementation of the Ricart-Agrawala Algorithm for mutual exclusion.
"""

__author__ = "Berker Acır"
__contact__ = "berkeracir159@gmail.com"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Berker Acır"]
__date__ = "2021/04/24"
__deprecated__ = False
__email__ = "berkeracir159@gmail.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

from enum import Enum
from time import sleep

from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessagePayload, GenericMessageHeader, inf, \
    Topology


class RicartAgrawalaEventTypes(Enum):
    REQUEST = "REQUEST"
    REPLY = "REPLY"
    PRIVILEGE = "PRIVILEGE"


class RicartAgrawalaMessageTypes(Enum):
    REQUEST = "REQUEST"
    REPLY = "REPLY"


class RicartAgrawalaMessageHeader(GenericMessageHeader):

    def __init__(self, messageType, messageFrom, messageTo, nextHop=float('inf'), interfaceID=float('inf'),
                 sequenceID=-1):
        super().__init__(messageType, messageFrom, messageTo, nextHop, interfaceID, sequenceID)


class RicartAgrawalaMessagePayload(GenericMessagePayload):

    def __init__(self, clock, nodeID):
        self.clock = clock
        self.nodeID = nodeID


class MutualExclusionAgrawalaComponent(ComponentModel):
    privilegeSleepAmount = 1

    def __init__(self, componentName, componentID):
        super().__init__(componentName, componentID)

        self.eventhandlers[RicartAgrawalaEventTypes.REQUEST] = self.request_received
        self.eventhandlers[RicartAgrawalaEventTypes.REPLY] = self.reply_received
        self.eventhandlers[RicartAgrawalaEventTypes.PRIVILEGE] = self.on_privilege

        self.clock = 0
        self.havePendingRequest = False
        self.pendingRequestClock = None
        self.isPrivileged = False

        self.deferredRequests = list()
        self.receivedReplies = set()
        self.otherNodeIDs = set()

        self.privilegeCount = 0
        self.sentRequestCount = 0
        self.sentReplyCount = 0
        self.receivedRequestCount = 0
        self.receivedReplyCount = 0
        self.forwardedMessageCount = 0

    def on_init(self, eventobj: Event):
        self.otherNodeIDs = set(Topology().nodes.keys())
        self.otherNodeIDs.remove(self.componentinstancenumber)

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        header = message.header
        messageType = header.messagetype
        messageTo = header.messageto

        if messageTo == self.componentinstancenumber:
            if messageType == RicartAgrawalaMessageTypes.REQUEST:
                eventobj.event = RicartAgrawalaEventTypes.REQUEST
                self.send_self(eventobj)
            elif messageType == RicartAgrawalaMessageTypes.REPLY:
                eventobj.event = RicartAgrawalaEventTypes.REPLY
                self.send_self(eventobj)
        else:
            nextHop = Topology().get_next_hop(self.componentinstancenumber, messageTo)
            interfaceID = f"{self.componentinstancenumber}-{nextHop}"

            if nextHop != inf and nextHop != self.componentinstancenumber:
                self.forwardedMessageCount += 1
                header.nexthop = nextHop
                header.interfaceid = interfaceID
                self.send_down(Event(self, EventTypes.MFRT, message))

    def request_received(self, eventobj: Event):
        self.receivedRequestCount += 1
        receivedRequestClock = eventobj.eventcontent.payload.clock
        receivedRequestNodeID = eventobj.eventcontent.payload.nodeID

        if not self.isPrivileged:   # Not privileged
            if self.havePendingRequest:     # Have pending request
                if receivedRequestClock < self.pendingRequestClock:
                    isMessageDeferred = False
                elif receivedRequestClock == self.pendingRequestClock and receivedRequestNodeID < self.componentinstancenumber:
                    isMessageDeferred = False
                else:
                    isMessageDeferred = True
            else:   # Does not have pending request
                isMessageDeferred = False
        else:   # Privileged
            isMessageDeferred = True

        if isMessageDeferred:
            self.deferredRequests.append(eventobj)
        else:
            if self.clock <= receivedRequestClock:
                self.clock = receivedRequestClock + 1
            self.send_reply(receivedRequestNodeID)

    def reply_received(self, eventobj: Event):
        self.receivedReplyCount += 1
        replyFrom = eventobj.eventcontent.payload.messagepayload
        self.receivedReplies.add(replyFrom)

        if len(self.receivedReplies) == len(self.otherNodeIDs):
            self.send_self(Event(self, RicartAgrawalaEventTypes.PRIVILEGE, None))
        elif len(self.receivedReplies) > len(self.otherNodeIDs):
            raise RuntimeError("Received reply message count exceeded expected limit!")

    def on_privilege(self, eventobj: Event):
        self.isPrivileged = True
        self.havePendingRequest = False
        self.receivedReplies.clear()

        self.privilegeCount += 1
        sleep(self.privilegeSleepAmount)

        self.isPrivileged = False
        self.send_replies_to_deferred_requests()

    def send_request(self):
        self.sentRequestCount += 1
        self.havePendingRequest = True
        self.pendingRequestClock = self.clock
        self.clock += 1

        for nodeID in self.otherNodeIDs:
            nextHop = Topology().get_next_hop(self.componentinstancenumber, nodeID)
            interfaceID = f"{self.componentinstancenumber}-{nextHop}"
            header = RicartAgrawalaMessageHeader(RicartAgrawalaMessageTypes.REQUEST, self.componentinstancenumber,
                                                 nodeID, nextHop, interfaceID)
            payload = RicartAgrawalaMessagePayload(self.pendingRequestClock, self.componentinstancenumber)
            message = GenericMessage(header, payload)
            self.send_down(Event(self, EventTypes.MFRT, message))

    def send_reply(self, nodeID):
        self.sentReplyCount += 1
        nextHop = Topology().get_next_hop(self.componentinstancenumber, nodeID)
        interfaceID = f"{self.componentinstancenumber}-{nextHop}"
        header = RicartAgrawalaMessageHeader(RicartAgrawalaMessageTypes.REPLY, self.componentinstancenumber, nodeID,
                                             nextHop, interfaceID)
        payload = GenericMessagePayload(self.componentinstancenumber)
        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))

    def send_replies_to_deferred_requests(self):
        while self.deferredRequests:
            event = self.deferredRequests.pop(0)
            deferredRequestNodeID = event.eventcontent.payload.nodeID
            deferredRequestClock = event.eventcontent.payload.clock

            if self.clock <= deferredRequestClock:
                self.clock = deferredRequestClock + 1
            self.send_reply(deferredRequestNodeID)
