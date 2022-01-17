"""Mutual Authentication using Interlock Protocol"""

import sys, os
import os
import sys

from networkx import algorithms

from ahc.Channels.Channels import Channel, P2PFIFOPerfectChannel

sys.path.insert(0, os.getcwd())

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from ahc.Ahc import ComponentRegistry
from enum import Enum
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import networkx, itertools, matplotlib.pyplot

registry = ComponentRegistry()

password_size = 64
pass_split = 32

class State(Enum):
    INIT = 0
    PUBLIC_KEY_SENT = 1
    FIRST_HALF_SENT = 2
    SECOND_HALF_SENT = 3
    AUTHENTICATED = 4
    

class Alice(ComponentModel):
    
    def __init__(self, componentname, componentinstancenumber, hA, hB, pA):
        self.alice_state = State.INIT
        self.private_alice = rsa.generate_private_key(65537, 2048)
        self.pA = pA
        self.hA = hA
        self.hB = hB
        super().__init__(componentname, componentinstancenumber)
    
    def on_init(self, eventobj: Event):
        pk = self.private_alice.public_key()
        pem = pk.public_bytes(encoding=serialization.Encoding.PEM, 
                              format=serialization.PublicFormat.SubjectPublicKeyInfo)
        evt = Event(self, EventTypes.MFRT, pem)
        self.send_down(evt)
        self.alice_state = State.PUBLIC_KEY_SENT
        print("Alice sends her public key to Bob")
        
    def on_message_from_bottom(self, eventobj: Event):
        if self.alice_state == State.PUBLIC_KEY_SENT:
            self.publickey_received = serialization.load_pem_public_key(eventobj.eventcontent)
            if isinstance(self.publickey_received, rsa.RSAPublicKey):
                print("Alice receives Bob's public key")
                self.encypted_pA = self.publickey_received.encrypt(
                    self.pA, 
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
                    )
                evt = Event(self, EventTypes.MFRT, self.encypted_pA[0:128])
                self.send_down(evt)
                self.alice_state = State.FIRST_HALF_SENT
                print("Alice sends first half of her password")
            else:
                print("Alice did not receive valid RSA Public Key")
        elif self.alice_state == State.FIRST_HALF_SENT:
            self.first_half = eventobj.eventcontent
            print("Alice receives first half of Bob's password")
            if isinstance(self.publickey_received, rsa.RSAPublicKey):
                evt = Event(self, EventTypes.MFRT, self.encypted_pA[128:])
                self.send_down(evt)
                self.alice_state = State.SECOND_HALF_SENT
                print("Alice sends second half of her password")
            else:
                print("Alice did not receive valid RSA Public Key")
        elif self.alice_state == State.SECOND_HALF_SENT:
            self.second_half = eventobj.eventcontent
            self.password_received = self.private_alice.decrypt(
                self.first_half + self.second_half,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(), 
                    label=None
                    )
                )
            print("Alice receives second half of Bob's password")
            digest = hashes.Hash(hashes.SHA256())
            digest.update(self.password_received)
            h = digest.finalize()
            if self.hB == h:
                print("Alice authenticated Bob")
                self.alice_state = State.AUTHENTICATED
            else:
                print("Alice received wrong password, raise alarm")
                self.alice_state = State.INIT
                return
        
class Bob(ComponentModel):
    
    def __init__(self, componentname, componentinstancenumber, hA, hB, pB):        
        self.bob_state = State.INIT
        self.private_bob = rsa.generate_private_key(65537, 2048)
        self.hA = hA
        self.hB = hB
        self.pB = pB
        super().__init__(componentname, componentinstancenumber)
        
    def on_message_from_bottom(self, eventobj: Event):
        if self.bob_state == State.INIT:
            self.publickey_received = serialization.load_pem_public_key(eventobj.eventcontent)
            if isinstance(self.publickey_received, rsa.RSAPublicKey):
                print("Bob receives Alice's public key")
                pk = self.private_bob.public_key()
                pem = pk.public_bytes(encoding=serialization.Encoding.PEM, 
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo)
                evt = Event(self, EventTypes.MFRT, pem)
                self.send_down(evt)
                self.bob_state = State.PUBLIC_KEY_SENT
                print("Bob sends his public key to Alice")
            else:
                print("Bob did not receive valid RSA Public Key")
        elif self.bob_state == State.PUBLIC_KEY_SENT:
            self.first_half = eventobj.eventcontent
            print("Bob receives first half of Alice's password")
            if isinstance(self.publickey_received, rsa.RSAPublicKey):
                self.encrypted_pB = self.publickey_received.encrypt(
                    self.pB,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
                    )
                evt = Event(self, EventTypes.MFRT, self.encrypted_pB[0:128])
                self.send_down(evt)
                self.bob_state = State.FIRST_HALF_SENT
                print("Bob sends first half of his password")
            else:
                print("Bob did not receive valid RSA Public Key")
        elif self.bob_state == State.FIRST_HALF_SENT:
            self.second_half = eventobj.eventcontent
            self.password_received = self.private_bob.decrypt(
                self.first_half + self.second_half,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(), 
                    label=None
                    )
                )
            print("Bob receives second half of Alice's password")
            digest = hashes.Hash(hashes.SHA256())
            digest.update(self.password_received)
            full_hash = digest.finalize()
            if self.hA == full_hash:
                self.bob_state = State.AUTHENTICATED
                print("Bob authenticated Alice")
            else:
                print("Bob receives wrong password")
                self.bob_state = State.INIT
                return
            if isinstance(self.publickey_received, rsa.RSAPublicKey):
                evt = Event(self, EventTypes.MFRT, self.encrypted_pB[128:])
                self.send_down(evt)
                self.bob_state = State.SECOND_HALF_SENT
                print("Bob sends second half of his password")
            else:
                print("Bob did not receive valid RSA Public Key")
        
def main():
    pA = os.urandom(password_size)
    pB = os.urandom(password_size)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(pA)
    hA = digest.finalize()
    digest = hashes.Hash(hashes.SHA256())
    digest.update(pB)
    hB = digest.finalize()
    topo = Topology()
    topo.nodes["Alice"] = Alice("Alice", 0, hA, hB, pA)
    topo.nodes["Bob"] = Bob("Bob", 1, hA, hB, pB)
    topo.channels["A-B"] = Channel("A-B", 2)
    topo.nodes["Alice"].connect_me_to_channel(ConnectorTypes.DOWN, topo.channels["A-B"])
    topo.nodes["Bob"].connect_me_to_channel(ConnectorTypes.DOWN, topo.channels["A-B"])
    topo.G = networkx.Graph()
    if isinstance(topo.G, networkx.Graph):
        topo.G.add_nodes_from(["Alice","Bob"])
        pairs = [["Alice", "Bob"]]
        topo.G.add_edges_from(pairs)
        networkx.draw(topo.G, with_labels= True, node_size = 1000)
        matplotlib.pyplot.draw()
        
    topo.start()
    
    #matplotlib.pyplot.savefig('plot.png')
    matplotlib.pyplot.show()
    while True: pass
    
if __name__ == '__main__':
    main()