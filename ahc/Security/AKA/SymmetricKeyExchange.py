import os
import sys
sys.path.insert(0, os.getcwd())
from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from cryptography.fernet import Fernet
from ahc.Channels.Channels import Channel
import networkx as nx
from time import sleep

"""    -----Schneier 3.1. Key Exchange: Key Exchange with Symmetric Cryptography------
    The protocol is as follows: Alice wants to communicate with Bob through a secure channel.
    Alice asks Trent(The Trusted 3rd Party) for a session key. Trent already shares secret
    keys with both Alice and Bob. Trent generates a session key for Alice and Bob and makes
    two copies of it. Encrypts one with Alice's the other with Bob's secret key, then
    sends both copies to Alice. Alice decrypts her copy and sends Bob his. Bob decrypts his copy
    and they both obtain the same session key in a secure way. Now they can communicate!
    The implementation also includes a pair message exchange after the key exchange for
    testing purposes.


    Generate Alice and Bob's secret keys that are shared with Trent"""

alice_key = Fernet.generate_key()
bob_key = Fernet.generate_key()


class Alice(ComponentModel):
    keys = {'secret': alice_key, 'session': -1}

    """Alice asks for a session key from Trent"""
    def on_init(self, eventobj: Event):
        sleep(1)
        print("---Communication Starts---\n")
        print("---Alice---\n")
        message_for_trent = "I need a session key!"
        message = [self.componentname, message_for_trent]
        print("Alice asked Trent for a session key.\n")
        evt = Event(self, EventTypes.MFRT, message)
        sleep(1)
        self.send_up(evt)

    """Alice receives message"""
    def on_message_from_bottom(self, eventobj: Event):
        print("---Alice---\n")
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        message = eventobj.eventcontent

        """Check if the sender is Trent or Bob"""
        if message[0] == "Trent":
            """Check if Trent sent the key"""
            if message[1] == "Here is your key Alice!":
                print(f"Alice received the session key!\n")
                session_key = Fernet(self.keys["secret"]).decrypt(message[2])
                self.keys["session"] = session_key
                bob_encrypted_key = message[3]
                message_for_bob = "Here is your copy of encrypted session key Bob!"
                encrypted_message = [self.componentname, message_for_bob, bob_encrypted_key]
                print(f"Alice sent Bob's copy of session key to him!\n")
                evt = Event(self, EventTypes.MFRT, encrypted_message)
                sleep(1)
                self.send_down(evt)
            else:
                """Check if the session key is already received"""
                if self.keys['session'] == -1:
                    print(f"Session key isn't received!\n")
                else:
                    print(f"Message isn't understood!\n")
        elif message[0] == "Bob":
            """"Check if Bob sent an encrypted message"""
            if message[1] == "Encrypted message from Bob":
                message_content = Fernet(self.keys["session"]).decrypt(message[2]).decode("utf-8")
                print(f"Message succesfully received from Bob : {message_content}\n")
                message_type = "Encrypted message from Alice"
                message_for_bob = "Hi Bob, long time no talk!"
                message_content = Fernet(self.keys["session"]).encrypt(message_for_bob.encode("utf-8"))
                encrypted_message = [self.componentname, message_type, message_content]
                print(f"Alice replied to Bob through the channel!\n")
                evt = Event(self, EventTypes.MFRT, encrypted_message)
                sleep(1)
                self.send_down(evt)
            else:
                print(f"Cannot detect encrypted message\n")
        else:
            print(f"Unidentified sender!\n")


class Trent(ComponentModel):
    keys = {'alice_secret': alice_key, 'bob_secret': bob_key}

    """Trent receives Alice's key request"""
    def on_message_from_bottom(self, eventobj: Event):
        print("---Trent---\n")
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        message = eventobj.eventcontent
        """Check if the sender is Alice"""
        if message[0] == "Alice":
            """Check if Alice wants a session key"""
            if message[1] == "I need a session key!":
                session_key = Fernet.generate_key()
                alice_encrypted_key = Fernet(self.keys["alice_secret"]).encrypt(session_key)
                bob_encrypted_key = Fernet(self.keys["bob_secret"]).encrypt(session_key)
                message_for_alice = "Here is your key Alice!"
                encrypted_message = [self.componentname, message_for_alice, alice_encrypted_key, bob_encrypted_key]
                print(f"Trent sent both session keys to Alice!\n")
                evt = Event(self, EventTypes.MFRT, encrypted_message)
                sleep(1)
                self.send_up(evt)
            else:
                print(f"Message isn't understood! Did you mean 'I need a session key!'?\n")
        else:
            print(f"Unidentified sender!\n")

class Bob(ComponentModel):
    keys = {'secret': bob_key, 'session': -1}

    """Bob receives message from Alice"""
    def on_message_from_bottom(self, eventobj: Event):
        print("---Bob---\n")
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        message = eventobj.eventcontent
        """Check if the sender is Alice"""
        if message[0] == "Alice":
            """Check if the message is the session key or an encrypted message"""
            if message[1] == "Here is your copy of encrypted session key Bob!":
                print(f"Bob also received the session key! Alice and Bob established a channel!\n")
                session_key = Fernet(self.keys["secret"]).decrypt(message[2])
                self.keys["session"] = session_key
                message_type = "Encrypted message from Bob"
                message_for_alice = "Hi Alice, It's Bob!"
                message_content = Fernet(self.keys["session"]).encrypt(message_for_alice.encode("utf-8"))
                encrypted_message = [self.componentname, message_type, message_content]
                print(f"Bob sent message to Alice through the channel!\n")
                evt = Event(self, EventTypes.MFRT, encrypted_message)
                sleep(1)
                self.send_down(evt)
            elif message[1] == "Encrypted message from Alice":
                message_content = Fernet(self.keys["session"]).decrypt(message[2]).decode("utf-8")
                print(f"Message succesfully received from Alice : {message_content}\n")
            else:
                if self.keys['session'] == -1:
                    print(f"Session key isn't received!\n")
                else:
                    print(f"Message isn't understood!\n")
        else:
            print(f"Unidentified sender!\n")
