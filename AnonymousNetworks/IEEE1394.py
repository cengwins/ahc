#!/usr/bin/env python

"""
Implementation of the "IEEE1394 (FireWire)" as described in the textbook
"Fokkink, Wan. Distributed algorithms: an intuitive approach. MIT Press,
2018.", first introduced in " IEEE 1394-1995 - IEEE Standard for a High
Performance Serial Bus"
"""

__author__ = "Yigit Sever"
__contact__ = "yigit@yigitsever.com"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Yigit Sever"]
__date__ = "2021-05-24"
__deprecated__ = False
__email__ = "yigit@yigitsever.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

import random
from enum import Enum
from random import randint
from time import sleep

from Ahc import (ComponentModel, Event, EventTypes, GenericMessage,
                 GenericMessageHeader, GenericMessagePayload, Topology)


class FireWirePacketType(Enum):
    """Two types of FireWire requests:
    - Parent Request
    - Acknowledgement"""

    PARENT_REQ = "PARENT_REQ"
    ACKNOWLEDGEMENT = "ACKNOWLEDGEMENT"


class FireWireMessageHeader(GenericMessageHeader):
    def __init__(
        self,
        messagefrom,
        messageto,
        messagetype="FireWire Message",
        nexthop=float("inf"),
        interfaceid=float("inf"),
        sequencenumber=-1,
    ):
        super().__init__(
            messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber
        )


class FireWireMessagePayload(GenericMessagePayload):
    def __init__(self):
        super().__init__(messagepayload="FireWire Message")


class FireWireNode(ComponentModel):

    holders = 0

    def __init__(self, component_name, component_id):
        super().__init__(component_name, component_id)

        self.parent = None
        self.received = list()
        self.neighbours = set()
        self.is_leader = False
        self.in_root_contention = True
        self.is_waiting = False
        self.is_terminated = False

    def on_init(self, eventobj: Event):
        self.neighbours = set(Topology().get_neighbors(self.componentinstancenumber))
        print(f"the neighbours of {self.componentinstancenumber} is {self.neighbours}")

        self.send_parent_req()

    def send_parent_req(self):
        """Send a parent request to the only eligible neighbour node. The
        neighbour node should not have sent this node a parent request and the
        number of such neighbours of this node should be 1.
        """
        # if there is *only* one possible parent then send them a parent request here

        result = self.neighbours - set(self.received)

        if len(result) == 1:
            par = result.pop()
            self.parent = par

            print(
                f"🤖 {self.componentinstancenumber} picked {self.parent} as it's parent"
            )

            next_hop_interface_id = f"{self.componentinstancenumber}-{self.parent}"

            header = FireWireMessageHeader(
                messagefrom=self.componentinstancenumber,
                messageto=self.parent,
                nexthop=self.parent,
                messagetype=FireWirePacketType.PARENT_REQ,
                interfaceid=next_hop_interface_id,
            )
            payload = FireWireMessagePayload()

            message = GenericMessage(header, payload)
            self.send_down(Event(self, EventTypes.MFRT, message))
        else:
            # Cannot send a parent request, more than one possible parent
            return

    def root_contention(self):
        print(f"🤖 {self.componentinstancenumber} is in ROOT CONTENTION")
        decision = random.choice([True, False])

        if decision:
            print(f"🤖 {self.componentinstancenumber} decides to YIELD")
            self.in_root_contention = True
            self.send_parent_req()
            self.is_waiting = False
        else:
            FireWireNode.holders += 1
            print(
                f"🤖 {self.componentinstancenumber} decides to HOLD "
                f" ({FireWireNode.holders} holders)"
            )
            self.is_waiting = True

            # can only save one of them currently
            # we need a proper timeout mechanism then we're done
            if FireWireNode.holders == 2:
                FireWireNode.holders = 0
                # timeout!
                self.root_contention()

    def on_message_from_bottom(self, eventobj: Event):
        """ New message from the link layer """
        header: FireWireMessageHeader = eventobj.eventcontent.header
        # paylaod is not important for FireWire

        if header.messagetype == FireWirePacketType.PARENT_REQ:
            if header.messagefrom is not self.parent:
                new_child = header.messagefrom

                self.received.append(new_child)

                next_hop_interface_id = f"{self.componentinstancenumber}-{new_child}"

                header = FireWireMessageHeader(
                    messagefrom=self.componentinstancenumber,
                    messageto=new_child,
                    nexthop=new_child,
                    messagetype=FireWirePacketType.ACKNOWLEDGEMENT,
                    interfaceid=next_hop_interface_id,
                )
                payload = FireWireMessagePayload()

                ack = GenericMessage(header, payload)
                self.send_down(Event(self, EventTypes.MFRT, ack))

                self.send_parent_req()
            elif not self.is_waiting:
                self.root_contention()
            else:
                print(f" 👑 {self.componentinstancenumber} is elected as the leader")
                self.is_leader = True
                self.is_terminated = True

        elif (
            header.messagetype == FireWirePacketType.ACKNOWLEDGEMENT
            and header.messagefrom == self.parent
        ):
            # This node's parent request got acknowledged, the process can
            # safely terminate
            print(
                f"🤖 {self.componentinstancenumber} received an ACK "
                f" from {header.messagefrom}, terminating"
            )
            self.is_terminated = True
            return
