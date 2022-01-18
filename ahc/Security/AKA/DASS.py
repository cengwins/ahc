from ahc.Ahc import ComponentModel, Event, ConnectorTypes, EventTypes, Topology
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet
import time
import sys
import os
from ahc.Channels.Channels import Channel

import json

def dict_to_bytes(dictionary):
    return json.dumps(dictionary).encode("utf-8")

def bytes_to_dict(bytes_object):
    return json.loads(bytes_object.decode("utf-8"))

private_key_Alice = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
)
public_key_Alice = private_key_Alice.public_key()

private_key_Bob = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
)
public_key_Bob = private_key_Bob.public_key()

private_key_Trent = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
)
public_key_Trent = private_key_Trent.public_key()

class Alice(ComponentModel):
    def on_init(self, eventobj: Event):
        message = {"name": "Bob"}
        msg_encoded = dict_to_bytes(message)
        event = Event(self, EventTypes.MFRB, msg_encoded)
        # time.sleep(1)
        # print("step1")
        self.send_up(event)

    def on_message_from_top(self, eventobj: Event): # gets message from Trent
        message = eventobj.eventcontent
        public_key_Trent.verify(
            message[1],
            message[0],
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        if message[0].split("|".encode("utf-8"))[0] != b"Bob":
            print("Wrong Public Key received, retry with true name")

        # gets bob public key from trent message
        bob_public = serialization.load_pem_public_key(message[0].split("|".encode("utf-8"))[1])

        # generates a session key and a public private key pair
        self.session_key = Fernet.generate_key()
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024,)
        self.public_key = self.private_key.public_key()

        # encypts time stamp with session key
        timestamp = str(time.time()).encode("utf-8")
        f = Fernet(self.session_key)
        encrypted_timestamp = f.encrypt(timestamp)

        # signs lifetime, alice name, and private key with alice private key
        self.lifetime = 3600
        lifetime = str(3600).encode("utf-8") # 1 hour
        alice_name = "Alice".encode("utf-8")
        LNP = lifetime + "|".encode("utf-8") + alice_name + "|".encode("utf-8") + self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        LNP_signed = private_key_Alice.sign(
            LNP,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # encrypts session key with bob public key and signs it with private key
        session_key_encoded = bob_public.encrypt(
            self.session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        signature = self.private_key.sign(
            session_key_encoded,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # data to be sent to bob
        message = [encrypted_timestamp, LNP, LNP_signed, session_key_encoded, signature]

        # sends message to bob
        # print("step3")
        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event) # from Alice to Node-1


    def on_message_from_bottom(self, eventobj: Event): # gets message from Node-1
        if type(eventobj.eventcontent) == bytes:
            message = eventobj.eventcontent
            f = Fernet(self.session_key)
            decrypted_timestamp = f.decrypt(message)
            decrypted_timestamp = float(decrypted_timestamp.decode("utf-8"))
            if (time.time() - decrypted_timestamp) > 10:
                print("Session expired")
                sys.exit()

            self.session_time = time.time()
            print("authenticated")
            content = input("Alice, enter your message: ")
            if content == "quit":
                os._exit(1)
            encrypted_content = f.encrypt(content.encode("utf-8"))
            new_message = ["message".encode("utf-8"), encrypted_content]

            event = Event(self, EventTypes.MFRT, new_message)
            self.send_down(event) # from Alice to Node-1

        elif type(eventobj.eventcontent) == list:
            if self.session_time + self.lifetime < time.time():
                print("Session expired")
                quit()

            message = eventobj.eventcontent

            f = Fernet(self.session_key)
            print("from bob to Alice: ", f.decrypt(message[1]).decode("utf-8"))
            content = input("Alice, enter your message: ")
            if content == "quit":
                os._exit(1)
            encrypted_content = f.encrypt(content.encode("utf-8"))
            new_message = ["message".encode("utf-8"), encrypted_content]

            event = Event(self, EventTypes.MFRT, new_message)
            self.send_down(event) # from Alice to Node-1


class Bob(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        message = eventobj.eventcontent

        if message[0].split("|".encode("utf-8"))[0] != b"Alice":
            print("Wrong Public Key received, retry with true name")

        # verify trent signature
        public_key_Trent.verify(
            message[1],
            message[0],
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # gets alice public key from trent message
        self.alice_public = serialization.load_pem_public_key(message[0].split("|".encode("utf-8"))[1])

        # verifies lifetime, alice name, and public key with alice public key
        self.alice_public.verify(
            self.message_from_alice[2],
            self.message_from_alice[1],
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        LNP = self.message_from_alice[1]
        lifetime, alice_name, public_key = LNP.split("|".encode("utf-8"))
        self.lifetime = int(lifetime.decode("utf-8"))
        alice_name = alice_name.decode("utf-8")

        public_key = serialization.load_pem_public_key(public_key)

        public_key.verify(
            self.message_from_alice[4],
            self.message_from_alice[3],
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        self.session_key = private_key_Bob.decrypt(
            self.message_from_alice[3],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        f = Fernet(self.session_key)
        timestamp = f.decrypt(self.message_from_alice[0])
        self.session_time = time.time()
        # print("step6 completed")

        if int(float(timestamp.decode("utf-8"))) + 10 < time.time():
            print("timestamp is not valid")
            print("no authentication")

        new_timestamp = f.encrypt(str(time.time()).encode("utf-8"))

        event = Event(self, EventTypes.MFRT, new_timestamp)
        self.send_down(event)

    def on_message_from_bottom(self, eventobj: Event):
        self.message_from_alice = eventobj.eventcontent

        if self.message_from_alice[0] != b"message":
            message = {"name": "Alice"}
            # print(type(self.message_from_alice))
            msg_encoded = dict_to_bytes(message)
            # print("step4")
            event = Event(self, EventTypes.MFRB, msg_encoded)
            self.send_up(event) # from Alice to Node-2

        else:
            if self.session_time + self.lifetime < time.time():
                print("session expired")
                os._exit(1)

            f = Fernet(self.session_key)
            print("from alice to bob: ", f.decrypt(self.message_from_alice[1]).decode("utf-8"))

            message = input("Bob, enter your message: ")
            if message == "quit":
                os._exit(1)
            encrypted_message = f.encrypt(message.encode("utf-8"))
            new_message = ["message".encode("utf-8"), encrypted_message]

            event = Event(self, EventTypes.MFRT, new_message)
            self.send_down(event)


class Trent(ComponentModel):
    def on_message_from_bottom(self, eventobj: Event):
        message_rcvd = bytes_to_dict(eventobj.eventcontent)
        if message_rcvd["name"] == "Bob":
            pem = public_key_Bob.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            msgg = "Bob".encode() + "|".encode("utf-8") + pem
            signature = private_key_Trent.sign(
                msgg,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            eventContent = [msgg, signature]

            event = Event(self, EventTypes.MFRT, eventContent)
            # print("step2")
            self.send_down(event)
        elif message_rcvd["name"] == "Alice":
            pem = public_key_Alice.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            msgg = "Alice".encode() + "|".encode("utf-8") + pem
            signature = private_key_Trent.sign(
                msgg,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            eventContent = [msgg, signature]

            event = Event(self, EventTypes.MFRT, eventContent)
            # print("step5")
            self.send_down(event)
        else:
            event = Event(self, EventTypes.MFRT, "name not recognized".encode("utf-8"))
            self.send_down(event)



class Node1(ComponentModel):
    def __init__(self, componentname, componentid):
        self.alice = Alice("Alice", componentid)
        self.trent = Trent("Trent", componentid)

        self.alice.connect_me_to_component(ConnectorTypes.UP, self.trent)
        self.trent.connect_me_to_component(ConnectorTypes.DOWN, self.alice)

        self.connect_me_to_component(ConnectorTypes.UP, self.alice)
        self.alice.connect_me_to_component(ConnectorTypes.DOWN, self)

        super().__init__(componentname, componentid)

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj)

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)


class Node2(ComponentModel):
    def __init__(self, componentname, componentid):
        self.bob = Bob("Bob", componentid)
        self.trent = Trent("Trent", componentid)

        self.bob.connect_me_to_component(ConnectorTypes.UP, self.trent)
        self.trent.connect_me_to_component(ConnectorTypes.DOWN, self.bob)

        self.connect_me_to_component(ConnectorTypes.UP, self.bob)
        self.bob.connect_me_to_component(ConnectorTypes.DOWN, self)

        super().__init__(componentname, componentid)

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj)

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)


sys.path.insert(0, os.getcwd())

def main():
    topo = Topology()
    topo.construct_sender_receiver(Node1, Node2, Channel)
    topo.start()
    print("Type quit to exit chat")

    while True: pass


if __name__ == "__main__":
    main()
