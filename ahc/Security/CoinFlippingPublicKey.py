from ahc.Ahc import *
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import secrets
import string
import random
from time import sleep
from ahc.Channels.Channels import Channel
from enum import Enum
from cryptography.hazmat.primitives import serialization
# Hakan Kanbur

alicePrivateKey = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
)
alicePublicKey = alicePrivateKey.public_key()

bobPrivateKey = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
)
bobPublicKey = bobPrivateKey.public_key()


class MessageTypes(Enum):
    RANDOM_ORDER_MESSAGE = 0
    BOB_ENC_MESSAGE = 1
    ALICE_DECY_MESSAGE = 2
    RESULT = 3
    ASKPAIR = 4


class Alice(ComponentModel):

    __name__ = "Alice"

    def on_init(self, eventobj: Event):
        num = 10  # define the length of the random string and generate it
        self.ranString1 = ''.join(secrets.choice(string.ascii_letters + string.digits)
                                  for x in range(num))
        self.ranString2 = ''.join(secrets.choice(string.ascii_letters + string.digits)
                                  for x in range(num))
        self.ranString1 = 'head' + self.ranString1
        self.ranString2 = 'tail' + self.ranString2
        self.encMessage1 = alicePublicKey.encrypt(self.ranString1.encode(), padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        ))
        self.encMessage2 = alicePublicKey.encrypt(self.ranString2.encode(), padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        ))
        header = GenericMessageHeader(
            MessageTypes.RANDOM_ORDER_MESSAGE, 0, 1, interfaceid="0-1")
        randomNum = random.randint(0, 1)
        # Choose message to send (Cannot send both because cannot decrypt it)
        if randomNum == 1:
            message = self.encMessage1
        else:
            message = self.encMessage2
        message1 = GenericMessage(header, message)
        event = Event(self, EventTypes.MFRT, message1)
        self.send_down(event)

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == MessageTypes.BOB_ENC_MESSAGE:
            message = alicePrivateKey.decrypt(eventobj.eventcontent.payload, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            ))
            # Cannot do it in bob because it gives ValueError("Encryption/decryption failed."), if we use high key_size then we cannot decrypt it in Alice because it gives us ValueError: Ciphertext length must be equal to key size..
            message = bobPublicKey.encrypt(message, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            ))

            header = GenericMessageHeader(
                MessageTypes.ALICE_DECY_MESSAGE, 0, 1, interfaceid="0-1")
            message1 = GenericMessage(header, message)
            event = Event(self, EventTypes.MFRT, message1)
            self.send_down(event)
        elif eventobj.eventcontent.header.messagetype == MessageTypes.RESULT:
            message = eventobj.eventcontent.payload.decode()
            if(message == self.ranString1 or message == self.ranString2):
                print("Nobody is cheated")
                print("Result is: " + message[:4])
            else:
                print("Somebody is cheated")
            print("Alice: My private key:" + alicePrivateKey.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode())
            header = GenericMessageHeader(
                MessageTypes.ASKPAIR, 0, 1, interfaceid="0-1")
            message1 = GenericMessage(header, message)
            event = Event(self, EventTypes.MFRT, message1)
            self.send_down(event)


class Bob(ComponentModel):
    __name__ = "Bob"

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == MessageTypes.RANDOM_ORDER_MESSAGE:
            self.message = eventobj.eventcontent.payload
            header = GenericMessageHeader(
                MessageTypes.BOB_ENC_MESSAGE, 1, 0, interfaceid="0-1")
            message1 = GenericMessage(header, self.message)
            event = Event(self, EventTypes.MFRT, message1)
            self.send_down(event)
        elif eventobj.eventcontent.header.messagetype == MessageTypes.ALICE_DECY_MESSAGE:
            message = bobPrivateKey.decrypt(eventobj.eventcontent.payload, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            ))
            header = GenericMessageHeader(
                MessageTypes.RESULT, 1, 0, interfaceid="0-1")
            message1 = GenericMessage(header, message)
            event = Event(self, EventTypes.MFRT, message1)
            self.send_down(event)
        else:
            print("Bob: My private key:" + bobPrivateKey.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode())


def main():
    topology = Topology()
    topology.construct_sender_receiver(Alice, Bob, Channel)
    topology.start()
    sleep(4)
    #while (True): pass


if __name__ == "__main__":
    main()
