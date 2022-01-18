import os
import sys
import time
import random
import codecs
from enum import Enum
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import cmac

sys.path.insert(0, os.getcwd())
sys.path.insert(1, (os.path.join(os.getcwd(), "../")))

import networkx as nx
import matplotlib.pyplot as plt

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

registry = ComponentRegistry()

class ApplicationLayerMessageTypes(Enum):
    # Alice initializes protocol by sending a random number Ra
    INITIALIZE = "INITIALIZE"
    # Bob receives Ra and sends Rb, Hk(Ra, Rb, B)
    RESPONSE = "RESPONSE"


class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


# Alice and Bob shares his component
class SharedComponent(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing\t{self.componentname}.{self.componentinstancenumber}")
        # Random numbers for Alice and Bob
        self.random_number = self.rng(8)
        
        # key for both encryption and CMAC
        self.key = b'iof-jbypHgi4dOgdjEZDGguKh3m4v2uEthrgbDsZ-2E='
        self.mac_key = b'\xf3\xf5\xad\xda\xac\x00q\xac\xd2\xaeR\x9b\xdb~\xf7`'
        
        # Initialize encryption primitive
        self.f = Fernet(self.key)

        # Initialize CMAC for MAC
        self.symmetric_mac = cmac.CMAC(algorithms.AES(self.mac_key)) 

        # Alice starts the protocol
        if self.componentinstancenumber == 0:
            self.onStartProtocol(destination=1, messagetype=ApplicationLayerMessageTypes.INITIALIZE)
        else:
            pass

    def on_message_from_bottom(self, eventobj: Event):
        try:
            # extract message header and content
            message = eventobj.eventcontent
            header = message.header

            if header.messagetype == ApplicationLayerMessageTypes.INITIALIZE:
                print(f"Component ({self.componentname}, {self.componentinstancenumber}) has received the {ApplicationLayerMessageTypes.INITIALIZE} message.")
                self.on_protocol_initialize(eventobj)
            
            elif header.messagetype == ApplicationLayerMessageTypes.RESPONSE:
                print(f"Component ({self.componentname}, {self.componentinstancenumber}) has received the {ApplicationLayerMessageTypes.RESPONSE} message.")
                self.on_response(eventobj)

        except AttributeError:
            print("Attribute Error")

    def on_protocol_initialize(self, eventobj: Event):
        # Alice send her random number to Bob
        if self.componentinstancenumber == 0:
            self.onAliceProtocolInitialize(destination=1, messagetype=ApplicationLayerMessageTypes.INITIALIZE)

        # Bob receives Alice's random number
        # Bob computes a MAC using CMAC function with parameters (R_a, R_b, Bob's Name)
        if self.componentinstancenumber == 1:
            self.onBobProtocolInitialize(destination=0, messagetype=ApplicationLayerMessageTypes.RESPONSE,
                                                        eventobj=eventobj)
        return

    def on_response(self, eventobj: Event):
        # When Alice receives a response
        # She will check if the receiver is really Bob
        # prints True if it is, False otherwise
        if self.componentinstancenumber == 0:
            self.onResponse(eventobj=eventobj)
        return

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers["initialize"] = self.on_protocol_initialize
        self.eventhandlers["response"] = self.on_response

    # Alice uses this function to start the protocol
    def onStartProtocol(self, destination, messagetype):
        header = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.INITIALIZE, 
                                                    self.componentinstancenumber, destination)
        payload = ApplicationLayerMessagePayload("Initialize")
        initialize_message = GenericMessage(header, payload)
        # randdelay = random.randint(0, 5)
        # time.sleep(randdelay)
        self.send_self(Event(self, "initialize", initialize_message))       
        return

    # Alice uses this function to send initialize message to Bob
    def onAliceProtocolInitialize(self, destination, messagetype):
        print(f"Component ({self.componentname}, {self.componentinstancenumber}) is inside the protocol_initialize.")
        
        # sends to Bob
        header = ApplicationLayerMessageHeader(messagetype, 
                                                self.componentinstancenumber, destination)
        
        # message to be sent
        msg = self.random_number
        
        # calculate hash of the message for integrity
        hash_msg = self.hash_message(msg)
        
        # add hash to the end of the message
        msg += hash_msg
        
        # encrypt random number
        cipher_text = self.encrypt(msg)
        payload = ApplicationLayerMessagePayload(cipher_text)
        
        initialize_message = GenericMessage(header, payload)
        
        # randdelay = random.randint(0, 5)
        # time.sleep(randdelay)
        
        self.send_down(Event(self, EventTypes.MFRT, initialize_message)) 
        return 

    # Bob uses this function to receive initialize message from Alice
    # and send response
    def onBobProtocolInitialize(self, destination, messagetype, eventobj: Event):
        print(f"Component ({self.componentname}, {self.componentinstancenumber}) is inside the protocol_initialize.")
        # send to Alice
        destination = 0

        # decrypt the received message
        received_message = self.decrypt(eventobj.eventcontent.payload.messagepayload) 
            
        # Alice's random number
        r_a = received_message[:8]

        # hash value
        hash_value = received_message[8:]

        # create MAC from CMAC
        mac = self.create_MAC(r_a + self.random_number + "Bob".encode())

        # message to be sent
        msg = "Bob".encode() + self.random_number + mac

        # hash message
        hash_msg = self.check_sum(r_a, hash_value)

        if hash_msg == True:
            print("Hash values match. ALice's message has not been altered.")
        elif hash_msg == False:
            print("Hash values match. Alice's message has been altered.")

        # add hash to the end of the message
        msg += self.hash_message(msg)

        header = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.RESPONSE, 
                                                        self.componentinstancenumber, destination)
            
        # encypt message
        cipher_text = self.encrypt(msg)
        payload = ApplicationLayerMessagePayload(cipher_text)
            
        initialize_message = GenericMessage(header, payload)
            
        # randdelay = random.randint(0, 5)
        # time.sleep(randdelay)

        self.send_down(Event(self, EventTypes.MFRT, initialize_message)) 
        return

    # Alice uses this function
    # When a response received from Bob
    # She checks if the sender of the response message is actually Bob
    # Protocol ends here
    def onResponse(self, eventobj: Event):
        print(f"Component ({self.componentname}, {self.componentinstancenumber}) is inside on response.")
            
        message = eventobj.eventcontent.payload.messagepayload
        decrypted_text = self.decrypt(message)
            
        # Bob's name
        bob_name = decrypted_text[:3].decode()

        # Bob's random number
        r_b = decrypted_text[3:11]
            
        # MAC from Bob
        mac = decrypted_text[11:27]

        # hashed message to check message integrity
        hashed_msg = decrypted_text[27:]

        check_hash = self.check_sum(decrypted_text[:27], hashed_msg)

        if check_hash == True:
            print("Hash values match. Bob's message has not been altered.")
        elif check_hash == False:    
            print("Hash values do not match. Bob's message has been altered.")

        check_mac = self.verify_MAC(self.random_number + r_b + bob_name.encode(), mac)
            
        if check_mac == True:
            print("Protocol ended successfully.")
            print("Alice knows that she is talking to Bob.")
        elif check_mac == False:
            print("Protocol failed.")
            print("Alice does not know who she is talking to.")
        
        return

    # HELPERS FOR CLASS
    # encrypt message to be sent
    # message is string
    def encrypt(self, message: bytes):
        cipher_text = self.f.encrypt(message)
        return cipher_text

    # decrypt message to be sent
    def decrypt(self, cipher_text: bytes):
        recovered_text = self.f.decrypt(cipher_text)
        return recovered_text

    # hash a message before send
    def hash_message(self, message: bytes):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(message)
        hashed_message = digest.finalize()
        return hashed_message

    # creates 16-bytes signature
    def create_MAC(self, message: bytes):
        self.symmetric_mac.update(message)
        signature = self.symmetric_mac.finalize()
        return signature

    # check if MAC's matches
    def verify_MAC(self, message: bytes, received_signature):
        self.symmetric_mac.update(message)
        try:
            self.symmetric_mac.verify(received_signature)
        except cryptography.exceptions.InvalidSignature:
            print('Invalid Signature')
            return False
        return True

    # check hash values to see if message content has been changed
    def check_sum(self, message: bytes, hashed_message: bytes):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(message)
        calculated_message = digest.finalize()
        if calculated_message == hashed_message:
            return True
        else:
            return False

    # random number generator
    def rng(self, size: int):
        random_number = os.urandom(size)
        return random_number


# Alice Node
class Alice(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing\t{self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = SharedComponent("ApplicationLayer", componentid)
        self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.UP, self)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
        
        super().__init__(componentname, componentid)


# Bob Node
class Bob(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing\t{self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appllayer = SharedComponent("ApplicationLayer", componentid)
        self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.UP, self)
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)
        
        super().__init__(componentname, componentid)


def main():
    # create nodeAlice
    # create nodeBob
    topo = Topology()
    topo.construct_sender_receiver(Alice, Bob, P2PFIFOPerfectChannel)
    topo.start()

    #while(True):
    #    pass
    time.sleep(5)

if __name__ == "__main__":
    main()