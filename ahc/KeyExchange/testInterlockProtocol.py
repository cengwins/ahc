# the project root must be in PYTHONPATH for imports
# $ export PYTHONPATH=$(pwd); python tests/KeyExchange/testInterlockProtocol.py

import networkx as nx
from ahc.Ahc import Topology
from ahc.Ahc import (ComponentModel, Event, Topology, GenericMessage, GenericMessageHeader, GenericMessagePayload,
                     EventTypes, ConnectorTypes)
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.KeyExchange.InterlockProtocol import (InterlockProtocol, InterlockProtocolPacketType,
                                               InterlockProtocolMessageHeader, InterlockProtocolMessagePayload,
                                               InterlockProtocolPublicKeyPayload)
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from time import sleep
import sys
from enum import Enum


class NaiveProtocol(ComponentModel):
    """
    This is just a simpler version of interlock protocol
    That encrypts message, sends it, receives a message and decrypts it
    """
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[InterlockProtocolPacketType.FIRST_PACKET] = self.on_first_packet
        self.eventhandlers[InterlockProtocolPacketType.KEY_PACKET] = self.on_key_packet

        self.messages = []
        self.sent_message_count = 0

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.other_side_public_key = None

        self.verbose = 0

    def on_init(self, eventobj: Event):
        self.messages = [f"message {i} from {self.componentname}" for i in range(3)]
        self.send_message(self.public_key, InterlockProtocolPacketType.KEY_PACKET)

    def on_message_from_peer(self, eventobj: Event):
        message_type = eventobj.eventcontent.header.messagetype
        received_from = eventobj.eventcontent.header.messagefrom
        if self.verbose:
            print(f"{self.componentname} received {message_type} from {received_from}")
        self.send_self(Event(self, message_type, eventobj.eventcontent))

    def on_first_packet(self, eventobj: Event):
        print(f"{self.componentname} received message:\"{self.decrypt(eventobj.eventcontent.payload.messagepayload)}\"")
        if self.sent_message_count == len(self.messages):
            if self.verbose:
                print("Messages finished")
            return
        self.send_message(self.encrypt(self.messages[self.sent_message_count]), InterlockProtocolPacketType.FIRST_PACKET)
        self.sent_message_count += 1

    def on_key_packet(self, eventobj: Event):
        self.other_side_public_key = eventobj.eventcontent.payload.messagepayload
        self.send_message(self.encrypt(self.messages[self.sent_message_count]), InterlockProtocolPacketType.FIRST_PACKET)
        self.sent_message_count += 1

    def encrypt(self, plaintext):
        ciphertext = self.other_side_public_key.encrypt(
            plaintext.encode('UTF-8'),                          # string->bytes conversion on plaintext
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt(self, ciphertext):
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('UTF-8')                        # bytes->string conversion on decrypted message

    def send_message(self, message_content, packet_type):
        header = InterlockProtocolMessageHeader(
            messagefrom=self.componentname,
            messageto=float("inf"),
            nexthop=float("inf"),
            messagetype=packet_type
        )
        if self.verbose:
            print(f"{self.componentname} sent packet with type {packet_type}")
        if packet_type == InterlockProtocolPacketType.KEY_PACKET:
            payload = InterlockProtocolPublicKeyPayload(message_content)
        else:
            payload = InterlockProtocolMessagePayload(message_content)
        message = GenericMessage(header, payload)
        self.send_peer(Event(self, EventTypes.MFRP, message))


# Malory can not use send_peer, since it would send messages to both Alice and Bob, so I created new connections
class MaloryConnectorTypes(Enum):
    ALICE = "ALICE"
    BOB = "BOB"


class ManInTheMiddle(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[InterlockProtocolPacketType.FIRST_PACKET] = self.on_first_packet
        self.eventhandlers[InterlockProtocolPacketType.SECOND_PACKET] = self.on_second_packet
        self.eventhandlers[InterlockProtocolPacketType.KEY_PACKET] = self.on_key_packet

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.alice_public_key = None
        self.bob_public_key = None

        # this is to imitate Alices and Bobs messages. Of course, in real world Malory would write better messages
        self.message = "Mallory did not write this"
        self.alice_first_message, self.alice_second_message = None, None    # To save imitated packets beforehand
        self.bob_first_message, self.bob_second_message = None, None
        self.alice_first_received_message = None                            # When received first half, to save
        self.bob_first_received_message = None                              # Similar to what we do in interlock prot.

        self.division_method = 1                                            # Same as interlock prot. division method
        self.working_mode = 1                                               # 0 -> decrypt/encrypt, 1 -> imitate
        self.verbose = 0                                                    # set to 1 for more output

    def send_alice(self, event: Event):
        """similar to send_down send_up but specific to alice"""
        try:
            for p in self.connectors[MaloryConnectorTypes.ALICE]:
                p.trigger_event(event)
        except:
            pass

    def send_bob(self, event: Event):
        """similar to send_down send_up but specific to bob"""
        try:
            for p in self.connectors[MaloryConnectorTypes.BOB]:
                p.trigger_event(event)
        except:
            pass

    def on_message_from_peer(self, eventobj: Event):
        """Same as interlock protocol"""
        message_type = eventobj.eventcontent.header.messagetype
        received_from = eventobj.eventcontent.header.messagefrom
        if self.verbose:
            print(f"{self.componentname} received {message_type} from {received_from}")
        self.send_self(Event(self, message_type, eventobj.eventcontent))

    def on_first_packet(self, eventobj: Event):
        message_type = eventobj.eventcontent.header.messagetype
        received_from = eventobj.eventcontent.header.messagefrom

        if self.working_mode == 0:
            """directly decrypt the message, read it and then encrypt it using target public key"""
            received_message = self.decrypt(eventobj.eventcontent.payload.messagepayload)
            print(f"{self.componentname} received message: \"{received_message}\"")
            target = "Bob" if received_from == "Alice" else "Alice"
            self.send_message(self.encrypt(received_message, target), message_type, target)
        else:
            """save the first packet and imitating the source send the target a message"""
            if received_from == "Alice":
                self.alice_first_received_message = eventobj.eventcontent.payload.messagepayload
                self.send_message(self.alice_first_message, message_type, "Bob")
            else:
                self.bob_first_received_message = eventobj.eventcontent.payload.messagepayload
                self.send_message(self.bob_first_message, message_type, "Alice")

    def on_second_packet(self, eventobj: Event):
        """
        zip and decrypt the received packets and send the second half of the imitated message, for which we have sent
        the first half for before.
        """
        received_from = eventobj.eventcontent.header.messagefrom
        message_type = eventobj.eventcontent.header.messagetype
        self.zip_and_decrypt(eventobj.eventcontent.payload.messagepayload, received_from)
        if received_from == "Alice":
            self.send_message(self.alice_second_message, message_type, "Bob")
        else:
            self.send_message(self.bob_second_message, message_type, "Alice")

    def zip_and_decrypt(self, second_received_packet, source):
        """
        Similar to what we do in interlock protocol, but added distinction for Alice and Bob
        """
        first_part = self.alice_first_received_message if source == "Alice" else self.bob_first_received_message
        if self.division_method == 0:
            message = self.decrypt(bytes([a | b for a, b in zip(first_part, second_received_packet)]))
            print(f"{self.componentname} received message: \"{message}\"")

        else:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(second_received_packet)
            hash_of_first_message = digest.finalize()
            if hash_of_first_message == first_part:
                message = self.decrypt(second_received_packet)
                print(f"{self.componentname} received message: \"{message}\"")
            else:
                print(f"{self.componentname} hashes do not match")

    def on_key_packet(self, eventobj: Event):
        """
        save the public key of source and send our public key to target
        also creates the imitated message. In real life imitated message would be created at every message received
        """
        received_from = eventobj.eventcontent.header.messagefrom
        if received_from == "Alice":
            self.alice_public_key = eventobj.eventcontent.payload.messagepayload                # save the public key
            self.send_message(self.public_key, InterlockProtocolPacketType.KEY_PACKET, "Bob")   # forward it
            # using alice's public key create imitated messages from Bob
            self.bob_first_message, self.bob_second_message = self.encrypt_and_divide(self.message, "Alice")
        else:
            self.bob_public_key = eventobj.eventcontent.payload.messagepayload
            self.alice_first_message, self.alice_second_message = self.encrypt_and_divide(self.message, "Bob")
            self.send_message(self.public_key, InterlockProtocolPacketType.KEY_PACKET, "Alice")

    def send_message(self, message_content, packet_type, target):
        """Similar to what we did in interlock protocol but added distinction for alice and bob"""
        header = InterlockProtocolMessageHeader(
            messagefrom="Alice" if target == "Bob" else "Bob",
            messageto=float("inf"),
            nexthop=float("inf"),
            messagetype=packet_type
        )
        if self.verbose:
            print(f"{self.componentname} sent packet with type {packet_type} to {target}")
        if packet_type == InterlockProtocolPacketType.KEY_PACKET:
            payload = InterlockProtocolPublicKeyPayload(message_content)
        else:
            payload = InterlockProtocolMessagePayload(message_content)
        message = GenericMessage(header, payload)
        if target == "Alice":
            self.send_alice(Event(self, EventTypes.MFRP, message))
        else:
            self.send_bob(Event(self, EventTypes.MFRP, message))

    def encrypt_and_divide(self, message, target):
        """Encrypt the message, divide it, return both halves"""
        ciphertext = self.encrypt(message, target)
        if self.division_method == 0:
            second_packet = bytes([i & 0b10101010 for i in ciphertext])  # take half the bits for every byte
            ciphertext = bytes([i & 0b01010101 for i in ciphertext])          # take the remaining half of the bits
        else:
            digest = hashes.Hash(hashes.SHA256())                             # creates the hash
            digest.update(ciphertext)                                         # takes the hash of ciphertext
            second_packet = ciphertext                                   # ciphertext is sent as second part
            ciphertext = digest.finalize()                                    # return the message digest to be sent 1st
        return ciphertext, second_packet

    def encrypt(self, plaintext, target):
        """Similar to what we did in interlock protocol but added distinction for alice and bob"""
        key = self.alice_public_key if target == "Alice" else self.bob_public_key
        ciphertext = key.encrypt(
            plaintext.encode('UTF-8'),                          # string->bytes conversion on plaintext
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt(self, ciphertext):
        """Same as interlock protocol"""
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('UTF-8')


class Node(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.is_interlock_protocol = 1          # 0 -> NaiveProtocol, 1 -> Interlock Protocol
        self.is_mallory_involved = 1            # 0 -> Mallory is not added to Node, 1 -> Mallory added
        self.division_method = 1                # 0 -> half the bits for every byte, 1 -> hashing
        self.mallory_working_mode = 1           # 0 -> just receive, decrypt, encrypt, send, 1 -> imitate source

        self.Alice = InterlockProtocol("Alice", 0) if self.is_interlock_protocol else NaiveProtocol("Alice", 0)
        self.Bob = InterlockProtocol("Bob", 1) if self.is_interlock_protocol else NaiveProtocol("Bob", 1)
        if self.is_interlock_protocol:
            self.Alice.division_method = self.division_method
            self.Alice.is_channel_mode = 0
            self.Bob.division_method = self.division_method
            self.Bob.is_channel_mode = 0

        if self.is_mallory_involved:
            self.Malory = ManInTheMiddle("Malory", componentinstancenumber)
            self.Malory.working_mode = self.mallory_working_mode
            self.Malory.division_method = self.division_method

            self.Alice.connect_me_to_component(ConnectorTypes.PEER, self.Malory)
            self.Bob.connect_me_to_component(ConnectorTypes.PEER, self.Malory)

            self.Malory.connect_me_to_component(MaloryConnectorTypes.ALICE, self.Alice)
            self.Malory.connect_me_to_component(MaloryConnectorTypes.BOB, self.Bob)
        else:
            self.Alice.connect_me_to_component(ConnectorTypes.PEER, self.Bob)
            self.Bob.connect_me_to_component(ConnectorTypes.PEER, self.Alice)


def main():
    G = nx.random_tree(2)
    topo = Topology()
    # creating topologies with different types of nodes is not straightforward, hence the
    # man-in-the-middle atacks are implemeted using simple node to start them comment out line 319
    # and run the command on line 318
    # topo.construct_single_node(Node, 0)
    topo.construct_from_graph(G, InterlockProtocol, P2PFIFOPerfectChannel)
    topo.start()
    while True:
        pass


if __name__ == "__main__":
    main()

