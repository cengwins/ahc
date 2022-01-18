import os
import sys

sys.path.insert(0, os.getcwd())

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from ahc.Ahc import ComponentRegistry
from cryptography.fernet import Fernet
import json
import time

registry = ComponentRegistry()

MAX_DELAY_IN_MS = 200

key1 = Fernet.generate_key()
key2 = Fernet.generate_key()


class Alice(ComponentModel):
    keys = {'Trent': key1}
    key_to_be_exchanged = Fernet.generate_key()

    def on_init(self, eventobj: Event):
        # Encrytion will be done by using Alice Trend shared key
        f = Fernet(self.keys['Trent'])
        # Before encrypting encryption body dictionary data type must be turned into bytes. It is done below.
        # (Time stamp, receiver_name are encrypted.
        tstamp = time.time() * 1000
        enc_body = f.encrypt(json.dumps({'time': tstamp, "receiver_name": "Bob"}).encode('utf-8'))
        # Key that will be given to final destionation) is encrypted.
        enc_key = f.encrypt(self.key_to_be_exchanged)
        # Sender Name and encrypred data body and key are combined.
        data_to_be_sent = [self.componentname, enc_body, enc_key]
        print("Alice -> Trent(Trust) : Encrypted Data with Session Key is Sending : ", data_to_be_sent)
        print('alice time stamp:', tstamp)
        evt = Event(self, EventTypes.MFRT, data_to_be_sent)
        self.send_down(evt)

    def on_message_from_bottom(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")


class Trent(ComponentModel):
    keys = {'Alice': key1, 'Bob': key2}

    #   def on_init(self, eventobj: Event):
    # evt = Event(self, EventTypes.MFRP, "Trent to peers")
    # self.send_peer(evt)

    def on_message_from_top(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        message = eventobj.eventcontent
        sender = message[0]
        shared_key_with_sender = self.keys[sender]
        f_alice_trent = Fernet(shared_key_with_sender)
        message_body = json.loads(f_alice_trent.decrypt(message[1]))
        message_key_in_bytes = f_alice_trent.decrypt(message[2])
        print('sender:', sender)
        print('message_body:', message_body)
        print('message_key:', message_key_in_bytes)

        receiver = message_body['receiver_name']
        shared_key_with_receiver = self.keys[receiver]
        f_trent_bob = Fernet(shared_key_with_receiver)
        tstamp = time.time() * 1000
        # Perform timestamp checking here
        if (tstamp - message_body['time'] < MAX_DELAY_IN_MS):
            enc_body = f_trent_bob.encrypt(json.dumps({'time': tstamp, "sender_name": "Alice"}).encode('utf-8'))
            print('trent time stamp', tstamp)
            print('time received passed the maximum delay test!')
            enc_key = f_trent_bob.encrypt(message_key_in_bytes)
            data_to_be_sent = [self.componentname, enc_body, enc_key]
            evt = Event(self, EventTypes.MFRT, data_to_be_sent)
            self.send_down(evt)
        else:
            print('Timestamp expired!')
            print('time received could not pass the maximum delay test!')

    def on_message_from_bottom(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        evt = Event(self, EventTypes.MFRB, "Trent to higher layer")
        self.send_up(evt)

    def on_message_from_peer(self, eventobj: Event):
        print(f"I am {self.componentname}, got message from peer, eventcontent={eventobj.eventcontent}\n")


class Bob(ComponentModel):
    keys = {'Trent': key2}
    key_to_be_exchanged = None

    def on_message_from_top(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}")
        message = eventobj.eventcontent
        f = Fernet(self.keys[message[0]])
        message_body = json.loads(f.decrypt(message[1]))
        message_key_in_bytes = f.decrypt(message[2])

        # Perform timestamp checking here
        tstamp = time.time() * 1000
        if (tstamp - message_body['time'] < MAX_DELAY_IN_MS):
            self.key_to_be_exchanged = {message_body['sender_name']: message_key_in_bytes}
            print('sender:', message[0])
            print('message_body:', message_body)
            print('message_key:', message_key_in_bytes)
            print('key_to_be_exchanged:', self.key_to_be_exchanged)
            print('Bob time stamp:', tstamp)
            print('time received passed the maximum delay test!')
        else:
            print('Timestamp expired!')
            print('time received could not pass the maximum delay test!')


class Node(ComponentModel):
    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS

        self.Alice = Alice("Alice", componentid)
        self.Trent = Trent("Trent", componentid)
        self.Bob = Bob("Bob", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.Alice.connect_me_to_component(ConnectorTypes.DOWN, self.Trent)
        self.Trent.connect_me_to_component(ConnectorTypes.UP, self.Alice)
        self.Trent.connect_me_to_component(ConnectorTypes.DOWN, self.Bob)
        self.Bob.connect_me_to_component(ConnectorTypes.UP, self.Trent)

        # Connect the bottom component to the composite component....
        self.Bob.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.Bob)
        super().__init__(componentname, componentid)


