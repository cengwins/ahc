import math
import struct

from ahc.Ahc import ComponentModel, Topology, Event, ConnectorTypes, EventTypes, ComponentRegistry
from ahc.Channels.Channels import Channel
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.fernet import Fernet
from threading import Semaphore
import time
import networkx as nx
# TODO: keys should be managed better
alicePrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
alicePublicKey = alicePrivateKey.public_key()
bobPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
bobPublicKey = bobPrivateKey.public_key()
trentPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
trentPublicKey = trentPrivateKey.public_key()

componentRegistry = ComponentRegistry()
semaphore = Semaphore(1)
startTime = time.time()
messageCount = 0
totalElapsedTime = 0


class Alice(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        receivedMessage = eventobj.eventcontent
        print(f'I am {self.componentname}, received message from Trent')

        bobData = receivedMessage[0]
        aliceData = receivedMessage[1]
        requestedPublicKey = bobData[0]
        signatureRequested = bobData[1]
        senderPublicKey = aliceData[0]
        signatureSender = aliceData[1]

        try:
            self.trentPublicKey.verify(signatureRequested,
                                       requestedPublicKey,
                                       padding.PSS(
                                           mgf=padding.MGF1(hashes.SHA256()),
                                           salt_length=padding.PSS.MAX_LENGTH
                                       ),
                                       hashes.SHA256())
        except InvalidSignature:
            print(f'I am {self.componentname}, first part of the received message is not valid!')
        print(f'I am {self.componentname}, first part of the received message is valid.')

        try:
            self.trentPublicKey.verify(signatureSender,
                                       senderPublicKey,
                                       padding.PSS(
                                           mgf=padding.MGF1(hashes.SHA256()),
                                           salt_length=padding.PSS.MAX_LENGTH
                                       ),
                                       hashes.SHA256())
        except InvalidSignature:
            print(f'I am {self.componentname}, second part of the received message is not valid!')
        print(f'I am {self.componentname}, second part of the received message is valid.')

        bobPublicKeyPEM = requestedPublicKey.split(b'!')[1]
        bobPublicKey: rsa.RSAPublicKey = load_pem_public_key(bobPublicKeyPEM)

        randomSessionKey = Fernet.generate_key()
        timeStamp = int(time.time())
        packedTimeStamp = struct.pack('>i', timeStamp)

        sessionInformation = bytes('Alice!', 'utf-8') + bytes('Bob!', 'utf-8') + randomSessionKey + bytes('!',
                                                                                                          'utf-8') + packedTimeStamp + bytes(
            '!', 'utf-8')

        signatureSession = self.privateKey.sign(sessionInformation,
                                                padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                            salt_length=padding.PSS.MAX_LENGTH),
                                                hashes.SHA256()
                                                )

        signedSessionInformation = bytes(len(sessionInformation).to_bytes(1, byteorder='big')) + bytes('!',
                                                                                                       'utf-8') + sessionInformation + signatureSession

        packets = []
        if len(signedSessionInformation) > 190:
            for i in range(math.ceil(len(signedSessionInformation) / 190)):
                encryptedSessionInformation = bobPublicKey.encrypt(signedSessionInformation[i * 190:i * 190 + 190],
                                                                   padding.OAEP(
                                                                       mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                       algorithm=hashes.SHA256(),
                                                                       label=None
                                                                   )
                                                                   )
                packets.append(encryptedSessionInformation)
        else:
            encryptedSessionInformation = bobPublicKey.encrypt(signedSessionInformation,
                                                               padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                            algorithm=hashes.SHA256(),
                                                                            label=None
                                                                            )
                                                               )
            packets.append(encryptedSessionInformation)

        message = [packets, bobData, aliceData]
        self.send_up(Event(self, EventTypes.MFRT, message))

        global messageCount
        if messageCount < 100:
            global startTime
            semaphore.acquire()
            message = ['Alice', 'Bob']
            print(f'I am {self.componentname}, sending message up: {message}')
            startTime = time.time()
            self.send_down(Event(self, EventTypes.MFRT, message))
            messageCount += 1

    def on_init(self, eventobj: Event):
        global startTime, messageCount
        semaphore.acquire()
        message = ['Alice', 'Bob']
        print(f'I am {self.componentname}, sending message up: {message}')
        startTime = time.time()
        self.send_down(Event(self, EventTypes.MFRT, message))
        messageCount += 1

    def __init__(self, componentname, componentinstancenumber):
        self.privateKey = alicePrivateKey
        self.trentPublicKey = trentPublicKey
        super().__init__(componentname, componentinstancenumber)


class Bob(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        print('!=')
        pass

    def on_message_from_bottom(self, eventobj: Event):
        receivedMessage = eventobj.eventcontent
        print(f'I am {self.componentname}, received message from top')

        packets = receivedMessage[0]
        requestedData = receivedMessage[1]
        senderData = receivedMessage[2]
        signatureRequested = requestedData[1]
        requestedPublicKey = requestedData[0]
        signatureSender = senderData[1]
        senderPublicKey = senderData[0]

        # Verify signature of Trent for (requested, requested public key) tuple
        try:
            self.trentPublicKey.verify(signatureRequested,
                                       requestedPublicKey,
                                       padding.PSS(
                                           mgf=padding.MGF1(hashes.SHA256()),
                                           salt_length=padding.PSS.MAX_LENGTH
                                       ),
                                       hashes.SHA256())
        except InvalidSignature:
            print(f'I am {self.componentname}, requested part of the received message is not valid!')
        print(f'I am {self.componentname}, requested part of the received message is valid.')

        # Verify signature of Trent for (sender, sender public key) tuple
        try:
            self.trentPublicKey.verify(signatureSender,
                                       senderPublicKey,
                                       padding.PSS(
                                           mgf=padding.MGF1(hashes.SHA256()),
                                           salt_length=padding.PSS.MAX_LENGTH
                                       ),
                                       hashes.SHA256())
        except InvalidSignature:
            print(f'I am {self.componentname}, sender part of the received message is not valid!')
        print(f'I am {self.componentname}, sender part of the received message is valid.')

        assert requestedData[0].split(b'!')[0] == b'Bob'  # Make sure incoming session information is meant for Bob

        senderName = senderData[0].split(b'!')[0]

        decryptedData = b''
        for packet in packets:
            data = self.privateKey.decrypt(packet,
                                           padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                        algorithm=hashes.SHA256(),
                                                        label=None)
                                           )

            decryptedData += data

        splitData = decryptedData.split(b'!')
        length = int.from_bytes(splitData[0], 'big')
        signature = decryptedData[length + 2:]
        sessionInformation = decryptedData[2:length + 2]

        senderPublicKey: rsa.RSAPublicKey = load_pem_public_key(senderData[0].split(b'!')[1])

        try:
            senderPublicKey.verify(signature,
                                   sessionInformation,
                                   padding.PSS(
                                       mgf=padding.MGF1(hashes.SHA256()),
                                       salt_length=padding.PSS.MAX_LENGTH
                                   ),
                                   hashes.SHA256())
        except InvalidSignature:
            print(f'I am {self.componentname}, session information is not valid!')
        print(f'I am {self.componentname}, session information is valid.')

        assert splitData[1] == senderName
        assert splitData[
                   2] == b'Bob'  # Make sure this session key was generated for communication between sender and Bob

        sessionKey = splitData[3]  # Random session key which can be used for secure communication

        packedTimeStamp = splitData[4]

        timeNow = time.time()
        unpackedTimeStamp = struct.unpack(">i", packedTimeStamp)[0]

        assert timeNow - unpackedTimeStamp <= 2  # Make sure timestamp is valid

        global startTime, messageCount, totalElapsedTime
        deltaTime = time.time() - startTime
        print(f'Time elapsed: {deltaTime}')
        totalElapsedTime += deltaTime
        if messageCount == 100:
            print(f'Average elapsed time: {totalElapsedTime / messageCount}')
        semaphore.release()

    def on_init(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber):
        self.privateKey = bobPrivateKey
        self.trentPublicKey = trentPublicKey
        super().__init__(componentname, componentinstancenumber)


class Trent(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        receivedMessage = eventobj.eventcontent
        print(f'I am {self.componentname}, received message from bottom: {receivedMessage}')

        sender = receivedMessage[0]
        requested = receivedMessage[1]

        senderPublicKeyDump = self.publicKeys[sender].public_bytes(serialization.Encoding.PEM,
                                                                   serialization.PublicFormat.SubjectPublicKeyInfo
                                                                   )

        requestedPublicKeyDump = self.publicKeys[requested].public_bytes(serialization.Encoding.PEM,
                                                                         serialization.PublicFormat.SubjectPublicKeyInfo
                                                                         )

        senderTuple = bytearray(sender, 'utf-8') + bytearray('!', 'utf-8') + bytearray(senderPublicKeyDump)
        requestedTuple = bytearray(requested, 'utf-8') + bytearray('!', 'utf-8') + bytearray(requestedPublicKeyDump)

        signatureSender = self.privateKey.sign(senderTuple,
                                               padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                           salt_length=padding.PSS.MAX_LENGTH),
                                               hashes.SHA256()
                                               )

        signatureRequested = self.privateKey.sign(requestedTuple,
                                                  padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                              salt_length=padding.PSS.MAX_LENGTH),
                                                  hashes.SHA256()
                                                  )

        transmitMessage = [(requestedTuple, signatureRequested), (senderTuple, signatureSender)]
        self.send_down(Event(self, EventTypes.MFRT, transmitMessage))

    def on_init(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber):
        self.publicKeys = {'Alice': alicePublicKey, 'Bob': bobPublicKey}
        self.privateKey = trentPrivateKey
        super().__init__(componentname, componentinstancenumber)


"""class Node(ComponentModel):
    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentinstancenumber):
        self.alice = Alice('Alice', componentinstancenumber)
        self.bob = Bob('Bob', componentinstancenumber)
        self.trent = Trent('Trent', componentinstancenumber)

        self.trent.connect_me_to_component(ConnectorTypes.DOWN, self.alice)
        self.alice.connect_me_to_component(ConnectorTypes.UP, self.trent)
        self.alice.connect_me_to_component(ConnectorTypes.DOWN, self.bob)
        self.bob.connect_me_to_component(ConnectorTypes.UP, self.alice)
        self.bob.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.bob)

        super().__init__(componentname, componentinstancenumber)
"""
