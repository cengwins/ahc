#!/usr/bin/env python

"""
Implementation of the "Kerberos" as described in the textbook
"Schneier, Bruce. Applied cryptography: protocols, algorithms,
 and source code in C. John Wiley & Sons, 2007 (20th Anniversary Edition)"
"""

__author__ = "Harun Poyraz"
__contact__ = "harun.poyraz@outlook.com"
__copyright__ = "Copyright 2022, WINSLAB"
__credits__ = ["Harun Poyraz"]
__date__ = "2022-??-??"
__deprecated__ = False
__email__ = "harun.poyraz@outlook.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

import datetime
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as spadding
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from ahc.Ahc import ComponentModel, Event, EventTypes, ConnectorList, ConnectorTypes, ComponentRegistry


class Client(ComponentModel):

    def __init__(self, component_name, component_id):
        self.privatekey = None
        self.keypairs = {}
        super().__init__(component_name, component_id)

    def connectMeToComponent(self, name, component):
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_init(self, eventobj: Event):
        #For testing
        if self.componentname == "Alice":
            reg = ComponentRegistry()
            trent = reg.get_component_by_key("Bob",0)
            self.create_connection_to_client(trent)
        pass

    def create_connection_to_client(self, peer):
        print("Connection from",self.unique_name()," starts to ",peer.unique_name()," Step 1")
        evt = Event(self, EventTypes.MFRB, (self, peer))
        self.send_up(evt)

    # message from kerberos
    def on_message_from_top(self, eventobj: Event):
        (EA, EB, messegareceiver) = eventobj.eventcontent
        if (messegareceiver == self.unique_name()):
            print("EA(T,L,K,B), EB(T,L,K,A) got. Step 2 done")
            plaintext = self.privatekey.decrypt(
                EA,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            asd = plaintext.split(b'xxx')
            current = datetime.datetime.now()

            T = datetime.datetime.strptime(asd[0].decode('utf-8'), '%Y-%m-%d %H:%M:%S.%f')

            L = datetime.datetime.strptime(asd[1].decode('utf-8'), '%H:%M:%S')
            L = datetime.timedelta(hours=L.hour, minutes=L.minute, seconds=L.second)

            if (current < (T + L)):

                receiver = asd[3].decode('utf-8')
                key = asd[2]

                self.keypairs[receiver] = (key, False)

                b = self.unique_name().encode('utf-8') + b"xxx" + asd[0]

                padder = spadding.PKCS7(128).padder()
                padded_data = padder.update(b)
                padded_data += padder.finalize()
                iv = os.urandom(16)
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                encryptor = cipher.encryptor()
                ct = encryptor.update(padded_data) + encryptor.finalize()
                print("EK(A,T),EB(T,L,K,A) created. Step 3")
                evt = Event(self, EventTypes.MFRP, (ct, EB, receiver, iv))
                self.send_peer(evt)
            else:
                pass

    def on_message_from_peer(self, eventobj: Event):

        if (len(eventobj.eventcontent) == 3):
            # ack
            (EK, receiver, iv) = eventobj.eventcontent
            if receiver == self.unique_name():
                self.keypairs[eventobj.eventsource.unique_name()] = (
                self.keypairs[eventobj.eventsource.unique_name()][0], True)

                cipher = Cipher(algorithms.AES(self.keypairs[eventobj.eventsource.unique_name()][0]), modes.CBC(iv))
                decryptor = cipher.decryptor()

                mes = decryptor.update(EK) + decryptor.finalize()
                unpadder = spadding.PKCS7(128).unpadder()
                data = unpadder.update(mes)
                data = data + unpadder.finalize()
                # data = T+1

                print("Step 4 done")
                print("Shared key is",self.keypairs[eventobj.eventsource.unique_name()][0])
        else:
            (EK, EB, receiver, iv) = eventobj.eventcontent
            if (receiver == self.unique_name()):
                print("EK(A,T),EB(T,L,K,A) got. Step 3 done")

                plaintext = self.privatekey.decrypt(
                    EB,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                asd = plaintext.split(b'xxx')

                receiver = asd[3].decode('utf-8')
                key = asd[2]
                self.keypairs[receiver] = (key, True)

                b = self.unique_name().encode('utf-8') + b"xxx" + asd[0]

                T = datetime.datetime.strptime(asd[0].decode('utf-8'), '%Y-%m-%d %H:%M:%S.%f')

                L = datetime.datetime.strptime(asd[1].decode('utf-8'), '%H:%M:%S')
                L = datetime.timedelta(hours=L.hour, minutes=L.minute, seconds=L.second)
                current = datetime.datetime.now()

                if (current < (T + L)):
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                    decryptor = cipher.decryptor()

                    mes = decryptor.update(EK) + decryptor.finalize()
                    unpadder = spadding.PKCS7(128).unpadder()
                    data = unpadder.update(mes)
                    data = data + unpadder.finalize()

                    # sent ack

                    padder = spadding.PKCS7(128).padder()
                    padded_data = padder.update(current.__str__().encode("utf-8"))
                    padded_data += padder.finalize()
                    iv = os.urandom(16)
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                    encryptor = cipher.encryptor()
                    ct = encryptor.update(padded_data) + encryptor.finalize()
                    print("EK(T + 1) created. Step 4")
                    evt = Event(self, EventTypes.MFRP, (ct, eventobj.eventsource.unique_name(), iv))
                    self.send_peer(evt)

        pass


class Kerberos(ComponentModel):
    def __init__(self):
        self.clientkeys = {}
        self.generatedkeys = {}
        super().__init__(
            "Trent", 0
        )

    def connectMeToComponent(self, name, component):

        try:
            self.connectors[name] = component

        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_init(self, eventobj: Event):
        pass

    def add_key_with_client(self, cli, key):
        self.clientkeys[cli.unique_name()] = key

    # message from clients
    def on_message_from_bottom(self, eventobj: Event):

        message = eventobj.eventcontent
        (sender, receiver) = message
        print("Messege got from ", sender.unique_name(), ". Who wants to connect ",receiver.unique_name(),"Step 1 done" )

        if self.clientkeys[sender.unique_name()]:
            if self.clientkeys[receiver.unique_name()]:

                timestamp = datetime.datetime.now().__str__()
                timestamp = timestamp.encode('utf-8')

                L = datetime.timedelta(minutes=5).__str__()
                L = L.encode('utf-8')

                key = os.urandom(32)

                B = receiver.unique_name().encode('utf-8')

                A = sender.unique_name().encode('utf-8')

                a = timestamp + b"xxx" + L + b"xxx" + key + b"xxx" + B

                b = timestamp + b"xxx" + L + b"xxx" + key + b"xxx" + A

                val1 = self.clientkeys[sender.unique_name()].encrypt(a, padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                ))
                val2 = self.clientkeys[receiver.unique_name()].encrypt(b, padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                ))
                print("EA(T,L,K,B), EB(T,L,K,A) created. Step 2")
                evt = Event(self, EventTypes.MFRT, (val1, val2, sender.unique_name()))
                self.send_down(evt)
                pass
            else:
                pass
        else:
            pass

class Node(ComponentModel):

    def __init__(self, componentname, componentid):
        self.kerberos = Kerberos()
        self.alice = Client("Alice", componentid)
        self.trent = Client("Bob", componentid)

        self.kerberos.connectMeToComponent(ConnectorTypes.DOWN, self.alice)
        self.kerberos.connectMeToComponent(ConnectorTypes.DOWN, self.trent)

        self.alice.connectMeToComponent(ConnectorTypes.PEER, self.trent)
        self.alice.connectMeToComponent(ConnectorTypes.UP, self.kerberos)

        self.trent.connectMeToComponent(ConnectorTypes.PEER, self.alice)
        self.trent.connectMeToComponent(ConnectorTypes.UP, self.kerberos)

        #Key Initilization
        private_key_alice = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,

        )
        public_key_alice = private_key_alice.public_key()
        self.alice.privatekey = private_key_alice
        self.kerberos.add_key_with_client(self.alice, public_key_alice)
        print("Key pair for Alice is created.")
        private_key_trent = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,

        )
        public_key_trent = private_key_trent.public_key()
        self.trent.privatekey = private_key_trent
        self.kerberos.add_key_with_client(self.trent, public_key_trent)
        print("Key pair for Trent is created.")
        super().__init__(componentname, componentid)



'''




class Client(ComponentModel):

    def __init__(self, component_name, component_id):
        self.privatekey = None
        self.keypairs = {}

        #testing
        self.finishtime = None
        super().__init__(component_name, component_id)

    def connectMeToComponent(self, name, component):
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_init(self, eventobj: Event):
        #For testing
        if self.componentname == "Alice":
            reg = ComponentRegistry()
            trent = reg.get_component_by_key("Trent",0)
            self.create_connection_to_client(trent)
        pass

    def create_connection_to_client(self, peer,keysiz,keylen):
        keysize = keysiz
        print("Connection from",self.unique_name()," starts to ",peer.unique_name()," Step 1")
        evt = Event(self, EventTypes.MFRB, (self, peer,keysiz,keylen))
        self.send_up(evt)

    # message from kerberos
    def on_message_from_top(self, eventobj: Event):
        (EA, EB, messegareceiver,keysize) = eventobj.eventcontent
        if (messegareceiver == self.unique_name()):
            print("EA(T,L,K,B), EB(T,L,K,A) got. Step 2 done")
            plaintext = self.privatekey.decrypt(
                EA,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            asd = plaintext.split(b'xxx')
            current = datetime.datetime.now()

            T = datetime.datetime.strptime(asd[0].decode('utf-8'), '%Y-%m-%d %H:%M:%S.%f')

            L = datetime.datetime.strptime(asd[1].decode('utf-8'), '%H:%M:%S')
            L = datetime.timedelta(hours=L.hour, minutes=L.minute, seconds=L.second)

            if (current < (T + L)):

                receiver = asd[3].decode('utf-8')
                key = asd[2]

                self.keypairs[receiver] = (key, False)

                b = self.unique_name().encode('utf-8') + b"xxx" + asd[0]

                padder = spadding.PKCS7(keysize).padder()
                padded_data = padder.update(b)
                padded_data += padder.finalize()
                iv = os.urandom(16)
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                encryptor = cipher.encryptor()
                ct = encryptor.update(padded_data) + encryptor.finalize()
                print("EK(A,T),EB(T,L,K,A) created. Step 3")
                evt = Event(self, EventTypes.MFRP, (ct, EB, receiver, iv,keysize))
                self.send_peer(evt)
            else:
                pass

    def on_message_from_peer(self, eventobj: Event):

        if (len(eventobj.eventcontent) == 4):
            # ack
            (EK, receiver, iv,keysize) = eventobj.eventcontent
            if receiver == self.unique_name():
                self.keypairs[eventobj.eventsource.unique_name()] = (
                self.keypairs[eventobj.eventsource.unique_name()][0], True)

                cipher = Cipher(algorithms.AES(self.keypairs[eventobj.eventsource.unique_name()][0]), modes.CBC(iv))
                decryptor = cipher.decryptor()

                mes = decryptor.update(EK) + decryptor.finalize()
                unpadder = spadding.PKCS7(keysize).unpadder()
                data = unpadder.update(mes)
                data = data + unpadder.finalize()
                # data = T+1

                print("Step 4 done")
                self.finishtime=datetime.datetime.now()
                print("Shared key is",self.keypairs[eventobj.eventsource.unique_name()][0])
        else:
            (EK, EB, receiver, iv,keysize) = eventobj.eventcontent
            if (receiver == self.unique_name()):
                print("EK(A,T),EB(T,L,K,A) got. Step 3 done")

                plaintext = self.privatekey.decrypt(
                    EB,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                asd = plaintext.split(b'xxx')

                receiver = asd[3].decode('utf-8')
                key = asd[2]
                self.keypairs[receiver] = (key, True)

                b = self.unique_name().encode('utf-8') + b"xxx" + asd[0]

                T = datetime.datetime.strptime(asd[0].decode('utf-8'), '%Y-%m-%d %H:%M:%S.%f')

                L = datetime.datetime.strptime(asd[1].decode('utf-8'), '%H:%M:%S')
                L = datetime.timedelta(hours=L.hour, minutes=L.minute, seconds=L.second)
                current = datetime.datetime.now()

                if (current < (T + L)):
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                    decryptor = cipher.decryptor()

                    mes = decryptor.update(EK) + decryptor.finalize()
                    print("paddsize = ",keysize)
                    unpadder = spadding.PKCS7(keysize).unpadder()
                    data = unpadder.update(mes)
                    data = data + unpadder.finalize()

                    # sent ack

                    padder = spadding.PKCS7(keysize).padder()
                    padded_data = padder.update(current.__str__().encode("utf-8"))
                    padded_data += padder.finalize()
                    iv = os.urandom(16)
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                    encryptor = cipher.encryptor()
                    ct = encryptor.update(padded_data) + encryptor.finalize()
                    print("EK(T + 1) created. Step 4")
                    evt = Event(self, EventTypes.MFRP, (ct, eventobj.eventsource.unique_name(), iv,keysize))
                    self.send_peer(evt)

        pass


class Kerberos(ComponentModel):
    def __init__(self):
        self.clientkeys = {}
        self.generatedkeys = {}
        super().__init__(
            "Trent", 0
        )

    def connectMeToComponent(self, name, component):

        try:
            self.connectors[name] = component

        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_init(self, eventobj: Event):
        pass

    def add_key_with_client(self, cli, key):
        self.clientkeys[cli.unique_name()] = key

    # message from clients
    def on_message_from_bottom(self, eventobj: Event):

        message = eventobj.eventcontent
        (sender, receiver,keysize,keylen) = message
        print("Messege got from ", sender.unique_name(), ". Who wants to connect ",receiver.unique_name(),"Step 1 done" )

        if self.clientkeys[sender.unique_name()]:
            if self.clientkeys[receiver.unique_name()]:

                timestamp = datetime.datetime.now().__str__()
                timestamp = timestamp.encode('utf-8')

                L = datetime.timedelta(minutes=5).__str__()
                L = L.encode('utf-8')

                key = os.urandom(keylen)
                print("keylen = ",keylen)
                B = receiver.unique_name().encode('utf-8')

                A = sender.unique_name().encode('utf-8')

                a = timestamp + b"xxx" + L + b"xxx" + key + b"xxx" + B

                b = timestamp + b"xxx" + L + b"xxx" + key + b"xxx" + A

                val1 = self.clientkeys[sender.unique_name()].encrypt(a, padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                ))
                val2 = self.clientkeys[receiver.unique_name()].encrypt(b, padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                ))
                print("EA(T,L,K,B), EB(T,L,K,A) created. Step 2")
                evt = Event(self, EventTypes.MFRT, (val1, val2, sender.unique_name(),keysize))
                self.send_down(evt)
                pass
            else:
                pass
        else:
            pass

class Node(ComponentModel):

    def __init__(self, componentname, componentid):
        self.kerberos = Kerberos()
        self.alice = Client("Alice", componentid)
        self.trent = Client("Bob", componentid)

        self.kerberos.connectMeToComponent(ConnectorTypes.DOWN, self.alice)
        self.kerberos.connectMeToComponent(ConnectorTypes.DOWN, self.trent)

        self.alice.connectMeToComponent(ConnectorTypes.PEER, self.trent)
        self.alice.connectMeToComponent(ConnectorTypes.UP, self.kerberos)

        self.trent.connectMeToComponent(ConnectorTypes.PEER, self.alice)
        self.trent.connectMeToComponent(ConnectorTypes.UP, self.kerberos)

        #Key Initilization
        private_key_alice = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,

        )
        public_key_alice = private_key_alice.public_key()
        self.alice.privatekey = private_key_alice
        self.kerberos.add_key_with_client(self.alice, public_key_alice)
        print("Key pair for Alice is created.")
        private_key_trent = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,

        )
        public_key_trent = private_key_trent.public_key()
        self.trent.privatekey = private_key_trent
        self.kerberos.add_key_with_client(self.trent, public_key_trent)
        print("Key pair for Trent is created.")
        super().__init__(componentname, componentid)
        
'''