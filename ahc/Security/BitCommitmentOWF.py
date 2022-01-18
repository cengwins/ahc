from enum import Enum
from time import time, sleep

import networkx

from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessageHeader, GenericMessage, Topology, ConnectorTypes
import hashlib
from secrets import SystemRandom

from ahc.Channels.Channels import Channel

BIT_LENGTH = 1024
BYTE_LENGTH = BIT_LENGTH // 8

start_time = 0


class MessageTypes(Enum):
    HASHED_AND_RANDOM = 0
    ORIGINAL = 1
    HASHED_RECEIVED = 2
    VALIDATION = 3


class Alice(ComponentModel):
    """
    On initialization Alice waits for an input.
    She generates two random bit strings.
    Concatenates random bit strings and the input.
    Then she hash this concatenated string and then
    send the hash value and first random bit string to the Bob.
    """

    def on_init(self, eventobj: Event):
        s = SystemRandom()
        self.first_random_bits = s.getrandbits(BIT_LENGTH).to_bytes(BYTE_LENGTH, 'big')
        self.second_random_bits = s.getrandbits(BIT_LENGTH).to_bytes(BYTE_LENGTH, 'big')
        bits_to_commit = input()
        global start_time
        start_time = time()
        bits_to_commit = bits_to_commit.encode()
        self.concatenated_bits = self.first_random_bits + self.second_random_bits + bits_to_commit
        hashed_message = hashlib.sha512(self.concatenated_bits).hexdigest()
        header = GenericMessageHeader(MessageTypes.HASHED_AND_RANDOM, 0, 1, interfaceid="0-1")
        data_to_sent = [hashed_message, self.first_random_bits]
        message = GenericMessage(header, data_to_sent)
        print("Alice -> Bob : Hashed message and random string sent: ", message)
        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event)

    """
    If the received message says that the hashed message is received
    Alice sends concatenated string to the Bob.
    If the received message says Valid that means the transaction is done.
    """

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == MessageTypes.HASHED_RECEIVED:
            header = GenericMessageHeader(MessageTypes.ORIGINAL, 0, 1, interfaceid="0-1")
            data_to_sent = [self.concatenated_bits]
            message = GenericMessage(header, data_to_sent)
            print("Alice -> Bob : Original string sent: ", message)
            event = Event(self, EventTypes.MFRT, message)
            self.send_down(event)
        elif eventobj.eventcontent.header.messagetype == MessageTypes.VALIDATION:
            finish_time = time()
            # print(f"microseconds passed = {(finish_time - start_time) * 1000000}")
            print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent.payload}\n")


class Bob(ComponentModel):
    """
    If the received message is hashed value and first random bit string
    they are stored for further evaluation.
    If the received message is original concatenated string Bob re-calculates the
    hash value and compare it to the hash value sent by Alice.
    If they are same a message sent to the Alice which says 'Valid'
    If they are not same a message sent to the Alice which says 'Invalid'
    """

    def on_message_from_bottom(self, eventobj: Event):

        if eventobj.eventcontent.header.messagetype == MessageTypes.HASHED_AND_RANDOM:
            self.hashed_message = eventobj.eventcontent.payload[0]
            self.first_random_bits = eventobj.eventcontent.payload[1]
            header = GenericMessageHeader(MessageTypes.HASHED_RECEIVED, 1, 0, interfaceid="0-1")
            message = "Hashed message received"
            data_to_sent = [message]
            message = GenericMessage(header, data_to_sent)
            print("Bob -> Alice : Hashed message received: ", message)
            event = Event(self, EventTypes.MFRT, message)
            self.send_down(event)

        elif eventobj.eventcontent.header.messagetype == MessageTypes.ORIGINAL:
            self.original_message = eventobj.eventcontent.payload[0]
            hashed_value = hashlib.sha512(self.original_message).hexdigest()
            if self.original_message[:BYTE_LENGTH] == self.first_random_bits and hashed_value == self.hashed_message:
                message = "Valid"
                data_to_sent = [message]
                header = GenericMessageHeader(MessageTypes.VALIDATION, 1, 0, interfaceid="0-1")
                message = GenericMessage(header, data_to_sent)
                print("Bob -> Alice : Original message received: ", message)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)

            else:
                message = "Invalid"
                data_to_sent = [message]
                header = GenericMessageHeader(MessageTypes.VALIDATION, 1, 0, interfaceid="0-1")
                message = GenericMessage(header, data_to_sent)
                print("Bob -> Alice : Original message received: ", message)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)


"""
Topology is created here.
"""

