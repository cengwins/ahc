#!/usr/bin/env python

"""
Implementation of the "Itai-Rodeh Election Algorithm for Rings" as
described in the textbook "Fokkink, Wan. Distributed algorithms: an intuitive
approach. MIT Press, 2018." with additional help from the paper "W. Fokkink and
J. Pang, Simplifying Itai-Rodeh Leader Election for Anonymous Rings. 2004."
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

from enum import Enum
from random import randint

from ahc.Ahc import (ComponentModel, Event, EventTypes, GenericMessage,
                 GenericMessageHeader, GenericMessagePayload, Topology)


class State(Enum):
    """
    State of the nodes, one from {active, passive, leader}
    - "active" nodes are initiators, attempting to become a leader
    - "passive" nodes have selected smaller id's than "active" nodes and cannot
      compete for leadership anymore
    - "leader" node has won an election round, only one such node should be
      present in the network
    """

    active = 1
    passive = 2
    leader = 3


class ItaiRodehMessageHeader(GenericMessageHeader):
    def __init__(
        self,
        messagefrom,
        messageto,
        messagetype="Itai-Rodeh Message",
        nexthop=float("inf"),
        interfaceid=float("inf"),
        sequencenumber=-1,
    ):
        super().__init__(
            messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber
        )


class ItaiRodehMessagePayload(GenericMessagePayload):
    """
    Itai-Rodeh Algorithm uses messages with 4 fields (using textbook's
    terminology here):

    - id_p (i): The (random) id the process has chosen for itself for the
      current round
    - election_round (n'): The current election round, old messages are
      silently dismissed
    - hop_count (h): Used so that the originating node can recognize their own
      message
    - dirty_bit (b): For resolving ties, nodes that picked this (highest) id
      will still be active next round
    """

    def __init__(self, election_round, id_p, messagepayload):
        super().__init__(messagepayload)
        self.election_round = election_round
        self.id_p = id_p
        self.hop_count = 1
        # disparity between the paper & textbook, following textbook here
        # mnemonic = bit is not dirty, we can still be the leader
        self.dirty_bit = False


class ItaiRodehNode(ComponentModel):
    """
    Node in a system that uses Itai-Rodeh algorithm
    Each process has three parameters:
    - id_p: 1 <= i <= N where N is the ring size
    - state: from the State enum, active nodes participate in the election,
      passive nodes pass messages around, leader is selected at the end of the
      election cycle
    - round: current election round, starts at 1
    """

    ring_size = 0
    callback = None
    draw_delay = None
    global_round = 1

    def __init__(self, component_name, component_id):
        super().__init__(component_name, component_id)

        """ The anonymous id the node will select for the round """
        self.id_p = 0

        """ Initially, all processes are active """
        self.state = State.active

        """ Initialized at round 0 """
        self.election_round = 1

    def send_election_packet(self):

        header = ItaiRodehMessageHeader(
            messagefrom=self.componentinstancenumber,
            messageto=self.next_hop,
            nexthop=self.next_hop,
            messagetype="ItaiRodeh Message",
            interfaceid=self.next_hop_interface_id
        )
        payload = ItaiRodehMessagePayload(self.election_round, self.id_p)

        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))

    def pass_packet_along(self, message):
        """For passive processes

        :message: the whole Event, with eventcontent which includes header and
        payload

        """
        pass

    def on_init(self, eventobj: Event):
        # Select an id for round 1
        self.id_p = randint(1, self.ring_size)
        print(
            f"🤖 {self.componentinstancenumber} selected {self.id_p} as their"
            f" ID for round {self.election_round}"
        )

        # Calculate the neighbour, we're on a directed ring
        self.neighbour_id = (int(self.componentinstancenumber) + 1) % self.ring_size

        self.next_hop = Topology().get_next_hop(
            self.componentinstancenumber, self.neighbour_id
        )

        self.next_hop_interface_id = f"{self.componentinstancenumber}-{self.next_hop}"

        self.send_election_packet()

    def on_message_from_bottom(self, eventobj: Event):
        """ New message from the link layer """
        payload: ItaiRodehMessagePayload = eventobj.eventcontent.payload
        header: ItaiRodehMessageHeader = eventobj.eventcontent.header

        message_election_round = payload.election_round
        message_assumed_id = payload.id_p

        # For the active node, we are going to follow the if/else chain given
        # in the textbook

        if self.state == State.passive:
            # passive node, pass the message on to the next hop, increase the
            # 'hop_count' of packet by one, no other responsibility
            payload.hop_count += 1
            header.messageto = self.next_hop
            header.next_hop = self.next_hop
            header.interfaceid = self.next_hop_interface_id

            message = GenericMessage(header, payload)
            self.send_down(Event(self, EventTypes.MFRT, message))
        elif self.state == State.active:

            if message_election_round > self.election_round or (
                message_election_round == self.election_round
                and message_assumed_id > self.id_p
            ):
                # Another node has picked a higher id than this node for the
                # current round or this node has received a message from a
                # future round, going passive

                print(
                    f"🤖 {self.componentinstancenumber} is PASSIVE: "
                    f"{message_assumed_id} for round {message_election_round} "
                    f"encountered, this node is at {self.election_round} with "
                    f"{self.id_p}"
                )

                self.state = State.passive
                # we clear the id_p here to have them *not* show up in the
                # animation
                self.id_p = " "
                payload.hop_count += 1

                header.messageto = self.next_hop
                header.next_hop = self.next_hop
                header.interfaceid = self.next_hop_interface_id

                message = GenericMessage(header, payload)
                self.send_down(Event(self, EventTypes.MFRT, message))

            elif message_election_round < self.election_round or (
                message_election_round == self.election_round
                and message_assumed_id < self.id_p
            ):
                # This node has received a message from a previous round or
                # from the current round but with a lower assumed id, so this
                # node can dismiss the election attempt of the sender node
                print(
                    f"🤖 {self.componentinstancenumber} is dismissing "
                    f"{message_assumed_id} for round {message_election_round} "
                    f"this node is at {self.election_round} with {self.id_p}"
                )

            elif (
                message_election_round == self.election_round
                and message_assumed_id == self.id_p
            ):

                if payload.hop_count < self.ring_size:
                    # receiver node is not the initial sender node
                    # another node has picked our id, dirty their bit and pass it along
                    payload.dirty_bit = True
                    payload.hop_count += 1

                    header.messageto = self.next_hop
                    header.next_hop = self.next_hop
                    header.interfaceid = self.next_hop_interface_id

                    print(
                        f"🤖 {self.componentinstancenumber} dirtied the bit "
                        f"for {message_assumed_id}, passing it along"
                    )
                    message = GenericMessage(header, payload)
                    self.send_down(Event(self, EventTypes.MFRT, message))

                elif payload.hop_count == self.ring_size:
                    # the message that this node has sent traversed all the way
                    # around the ring
                    print(
                        f"🤖 {self.componentinstancenumber}'s message "
                        f"traversed all the way around"
                    )
                    if payload.dirty_bit:
                        # Bit has been dirtied, next round
                        self.id_p = randint(1, self.ring_size)
                        self.election_round += 1
                        ItaiRodehNode.global_round = self.election_round
                        print(
                            f"🤖 {self.componentinstancenumber} is moving "
                            f"onto round {self.election_round}"
                        )
                        print(
                            f"🤖 {self.componentinstancenumber} selected "
                            f"{self.id_p} as their ID for round "
                            f"{self.election_round}"
                        )
                        self.send_election_packet()
                    else:
                        # The bit is still false, this node is the leader
                        self.state = State.leader
                        print(
                            f"🤖 {self.componentinstancenumber}: I'M THE ELECTED LEADER"
                        )
        self.callback.set()
        self.draw_delay.wait()
        self.draw_delay.clear()
