from ahc.Ahc import ComponentModel, Event, Topology, GenericMessage, GenericMessageHeader, GenericMessagePayload, EventTypes
from enum import Enum
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes


class InterlockProtocolPacketType(Enum):
    """
    Three types of Interlock Protocol packets:
    - KEY_PACKET: when node is sending its public key to other side
    - FIRST_PACKET: when the first part of message is being sent to other side
    - SECOND_PACKET: when the second part of message is being sent to other side
    """

    FIRST_PACKET = "FIRST_PACKET"
    SECOND_PACKET = "SECOND_PACKET"
    KEY_PACKET = "KEY_PACKET"


class InterlockProtocolMessageHeader(GenericMessageHeader):
    def __init__(self,
                 messagetype,
                 messagefrom,
                 messageto,
                 interfaceid='inf',
                 nexthop=float('inf'),
                 sequencenumber=-1):
        super().__init__(messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber)


class InterlockProtocolMessagePayload(GenericMessagePayload):
    def __init__(self, encrypted_message):
        super().__init__(messagepayload=encrypted_message)


class InterlockProtocolPublicKeyPayload(GenericMessagePayload):
    def __init__(self, public_key: rsa.RSAPublicKey):
        super().__init__(messagepayload=public_key)


class InterlockProtocol(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[InterlockProtocolPacketType.FIRST_PACKET] = self.on_first_packet
        self.eventhandlers[InterlockProtocolPacketType.SECOND_PACKET] = self.on_second_packet
        self.eventhandlers[InterlockProtocolPacketType.KEY_PACKET] = self.on_key_packet

        # division method 0: first packet is half the bits for every byte, second packet is the other half
        # division method 1: first packet is the hash of encrypted message, second packet is the encrypted message
        self.division_method = 1

        # Designating who will be the first one to send the first FIRST_PACKET
        self.is_first_sender = 1 if self.componentinstancenumber == 0 else 0
        self.messages = []
        self.sent_message_count = 0

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.other_side_public_key = None

        # Keeps track of the first received packet, so when we get the second half we can bring them together
        self.first_received_packet = None
        # saves the second part of the message that will be sent after the other side corresponds to first packet
        self.second_packet = None

        self.is_channel_mode = 1
        self.verbose = 0

    def on_init(self, eventobj: Event):
        """
        creates messages to be sent: message content can be changed, this is a mock message content
        send our public key to the neighbor
        """
        self.messages = [f"message {i} from {self.componentname}" for i in range(3)]
        self.send_message(self.public_key, InterlockProtocolPacketType.KEY_PACKET)

    def on_message_from_bottom(self, eventobj: Event):
        """
        depending on the message type send the event to self
        """
        message_type = eventobj.eventcontent.header.messagetype
        received_from = eventobj.eventcontent.header.messagefrom
        if self.verbose:
            print(f"{self.componentname} received {message_type} from {received_from}")
        self.send_self(Event(self, message_type, eventobj.eventcontent))

    def on_message_from_peer(self, eventobj: Event):
        """
        depending on the message type send the event to self
        """
        message_type = eventobj.eventcontent.header.messagetype
        received_from = eventobj.eventcontent.header.messagefrom
        if self.verbose:
            print(f"{self.componentname} received {message_type} from {received_from}")
        self.send_self(Event(self, message_type, eventobj.eventcontent))

    def on_key_packet(self, eventobj: Event):
        """
        Saves other sides public key. Then if we are the first sender, we start sending our first message.
        Note that sending message does not have to start here. With necessary changes sending messages can start with
        any other event
        """
        self.other_side_public_key = eventobj.eventcontent.payload.messagepayload
        if self.is_first_sender:
            self.encrypt_and_send()

    def on_first_packet(self, eventobj: Event):
        """
        Saves the first received packet, then if we are first sender, receiving other sides first packet means we can
        send our second packet. If we are not the first sender, we should send our first packet
        """
        self.first_received_packet = eventobj.eventcontent.payload.messagepayload
        if self.is_first_sender:
            self.send_message(self.second_packet, InterlockProtocolPacketType.SECOND_PACKET)
        else:
            self.encrypt_and_send()

    def on_second_packet(self, eventobj: Event):
        """
        Zips the first received packet and this one to get the whole message. Then if we are the first sender and
        received other sides second packet, we can move on to sending a new message, If we are not the first sender,
        we should send our second packet.
        """
        self.zip_and_decrypt(eventobj.eventcontent.payload.messagepayload)
        if self.is_first_sender:
            self.encrypt_and_send()
        else:
            self.send_message(self.second_packet, InterlockProtocolPacketType.SECOND_PACKET)

    def encrypt_and_send(self):
        """
        Checks if any messages left. If so, encrypts the message, saves the second packet and sends the first packet
        """
        if self.sent_message_count == len(self.messages):
            if self.verbose:
                print("Messages finished")
            return
        plaintext = self.messages[self.sent_message_count]
        self.sent_message_count += 1
        ciphertext = self.encrypt(plaintext)

        if self.division_method == 0:
            self.second_packet = bytes([i & 0b10101010 for i in ciphertext])  # take half the bits for every byte
            ciphertext = bytes([i & 0b01010101 for i in ciphertext])          # take the remaining half of the bits
        else:
            digest = hashes.Hash(hashes.SHA256())                             # creates the hash
            digest.update(ciphertext)                                         # takes the hash of ciphertext
            self.second_packet = ciphertext                                   # ciphertext is sent as second part
            ciphertext = digest.finalize()                                    # return the message digest to be sent 1st

        self.send_message(ciphertext, InterlockProtocolPacketType.FIRST_PACKET)

    def zip_and_decrypt(self, second_received_packet):
        """
        Brings the first and second halves of the messages together and prints necessary information
        """
        # division method: 0 -> for every byte half the bits are correct and the remaining bits are zero
        # taking the or for every byte will zip the messages, then we can apply decrypt
        if self.division_method == 0:
            message = self.decrypt(bytes([a | b for a, b in zip(self.first_received_packet, second_received_packet)]))
            print(f"{self.componentname} received message: \"{message}\"")

        # division method: 1 ->Second received packet is our encrypted message, take hash of it in and compare it to
        # first half. If they match, there is no problem, else the message or hash is changed.
        else:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(second_received_packet)
            hash_of_first_message = digest.finalize()
            if hash_of_first_message == self.first_received_packet:
                message = self.decrypt(second_received_packet)
                print(f"{self.componentname} received message: \"{message}\"")
            else:
                print(f"{self.componentname} hashes do not match")

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
        """
        Prepares the header and the payload and sends message to peer
        """
        next_hop_interface_id = f"{self.componentinstancenumber}-{1-self.componentinstancenumber}"
        header = InterlockProtocolMessageHeader(
            messagefrom=self.componentname,
            messageto=float("inf"),
            nexthop=float("inf"),
            messagetype=packet_type,
            interfaceid=next_hop_interface_id
        )
        if self.verbose:
            print(f"{self.componentname} sent packet with type {packet_type}")
        if packet_type == InterlockProtocolPacketType.KEY_PACKET:
            payload = InterlockProtocolPublicKeyPayload(message_content)
        else:
            payload = InterlockProtocolMessagePayload(message_content)
        message = GenericMessage(header, payload)
        if self.is_channel_mode:
            self.send_down(Event(self, EventTypes.MFRT, message))
        else:
            self.send_peer(Event(self, EventTypes.MFRP, message))
