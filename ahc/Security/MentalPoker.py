from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessageHeader, GenericMessage, Topology, ConnectorTypes
from ahc.Channels.Channels import Channel

from time import time, sleep

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from enum import Enum
import networkx
import string
import secrets
import random

#Generate public-private key pairs for each player
alicePrivateKey = rsa.generate_private_key(
     public_exponent=65537,
     key_size=2048,
)
alicePublicKey = alicePrivateKey.public_key()

bobPrivateKey = rsa.generate_private_key(
     public_exponent=65537,
     key_size=2048,
)
bobPublicKey = bobPrivateKey.public_key()

carolPrivateKey = rsa.generate_private_key(
     public_exponent=65537,
     key_size=2048,
)
carolPublicKey = carolPrivateKey.public_key()

#Whole alphabet for unique random string
alphabet = string.ascii_letters + string.digits

#Enumerations for different message types
class DealerMessageType(Enum):
    DECK_DEAL = 0
    DECRYPT_OPP_HAND = 1

class PlayerMessageType(Enum):
    RANDOM_ENC_HAND = 0
    REMAINING_CARDS = 1
    DEALER_HAND = 2
    CONFIRM_HAND = 3

#Components

class Alice(ComponentModel):

    hand = []

    def on_init(self, eventobj: Event):
        self.deck = "CA,C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,CJ,CQ,CK,DA,D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,DJ,DQ,DK,SA,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,SJ,SQ,SK,HA,H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,HJ,HQ,HK".split(",")
        self.randomString = []
        for i in range(52):
            pad = "0" if i < 10 else ""
            self.randomString.append(pad + str(i) + ''.join(secrets.choice(alphabet) for j in range(9)))
            card = self.deck[i]
            message = self.randomString[i] + card
            self.deck[i] = alicePublicKey.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

        header = GenericMessageHeader(DealerMessageType.DECK_DEAL, 0, 1, interfaceid="0-1")
        for i in range(52):
            message = GenericMessage(header, self.deck.pop(0))
            event = Event(self, EventTypes.MFRT, message)
            self.send_down(event)

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == PlayerMessageType.RANDOM_ENC_HAND:
            card = alicePrivateKey.decrypt(
                eventobj.eventcontent.payload,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            if eventobj.eventcontent.header.messagefrom == 1:
                card = bobPublicKey.encrypt(
                    card,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                header = GenericMessageHeader(DealerMessageType.DECRYPT_OPP_HAND, 0, 1, interfaceid="0-1")
                message = GenericMessage(header, card)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)

            elif eventobj.eventcontent.header.messagefrom == 2:
                card = carolPublicKey.encrypt(
                    card,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                header = GenericMessageHeader(DealerMessageType.DECRYPT_OPP_HAND, 0, 2, interfaceid="0-2")
                message = GenericMessage(header, card)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)

        elif eventobj.eventcontent.header.messagetype == PlayerMessageType.DEALER_HAND:
            card = alicePrivateKey.decrypt(
                eventobj.eventcontent.payload,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode()
            self.hand.append(card)

            if card[:11] not in self.randomString:
                print("Carol has given wrong cards to dealer")

            if len(self.hand) == 5:
                print("Alice's hand: ",end="")
                for card in self.hand:
                    print(card[11:], end=" ")
                print()

        elif eventobj.eventcontent.header.messagetype == PlayerMessageType.CONFIRM_HAND:
            randomStringCard = eventobj.eventcontent.payload[:11]
            if randomStringCard not in self.randomString:
                if eventobj.eventcontent.header.messagefrom == 1:
                    print("Bob is cheating")
                elif eventobj.eventcontent.header.messagefrom == 2:
                    print("Carol is cheating")


class Bob(ComponentModel):

    hand = []
    deck = []

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == DealerMessageType.DECK_DEAL:
            self.deck.append(eventobj.eventcontent.payload)
            if len(self.deck) == 52:
                header = GenericMessageHeader(PlayerMessageType.RANDOM_ENC_HAND, 1, 0, interfaceid="0-1")
                for i in range(5):
                    card = random.choice(self.deck)
                    self.deck.remove(card)
                    message = GenericMessage(header, card)
                    event = Event(self, EventTypes.MFRT, message)
                    self.send_down(event)

                # #Send own cards as straight(cheating)
                # for i in range(5):
                #     randomString = ''.join(secrets.choice(alphabet) for j in range(9))
                #     card = randomString + "C" + str(i)
                #     card = alicePublicKey.encrypt(
                #         card.encode(),
                #         padding.OAEP(
                #             mgf=padding.MGF1(algorithm=hashes.SHA256()),
                #             algorithm=hashes.SHA256(),
                #             label=None
                #         )
                #     )
                #     message = GenericMessage(header, card)
                #     event = Event(self, EventTypes.MFRT, message)
                #     self.send_down(event)


                header = GenericMessageHeader(PlayerMessageType.REMAINING_CARDS, 1, 2, interfaceid="1-2")
                for i in range(47):
                    message = GenericMessage(header, self.deck.pop(0))
                    event = Event(self, EventTypes.MFRT, message)
                    self.send_down(event)

        elif eventobj.eventcontent.header.messagetype == DealerMessageType.DECRYPT_OPP_HAND and eventobj.eventcontent.header.messageto == 1:
                card = bobPrivateKey.decrypt(
                    eventobj.eventcontent.payload,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode()
                self.hand.append(card)
                if len(self.hand) == 5:
                    print("Bob's hand: ",end="")
                    for card in self.hand:
                        print(card[11:], end=" ")
                    print()

                header = GenericMessageHeader(PlayerMessageType.CONFIRM_HAND, 1, 2, interfaceid="1-2")
                message = GenericMessage(header, card)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)

class Carol(ComponentModel):

    hand = []
    deck = []

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == PlayerMessageType.REMAINING_CARDS:
            self.deck.append(eventobj.eventcontent.payload)
            if len(self.deck) == 47:
                header = GenericMessageHeader(PlayerMessageType.RANDOM_ENC_HAND, 2, 0, interfaceid="0-2")
                for i in range(5):
                    card = random.choice(self.deck)
                    self.deck.remove(card)
                    message = GenericMessage(header, card)
                    event = Event(self, EventTypes.MFRT, message)
                    self.send_down(event)

                header = GenericMessageHeader(PlayerMessageType.DEALER_HAND, 2, 0, interfaceid="0-2")
                for i in range(5):
                    card = random.choice(self.deck)
                    self.deck.remove(card)
                    message = GenericMessage(header, card)
                    event = Event(self, EventTypes.MFRT, message)
                    self.send_down(event)

        elif eventobj.eventcontent.header.messagetype == DealerMessageType.DECRYPT_OPP_HAND and eventobj.eventcontent.header.messageto == 2:
                card = carolPrivateKey.decrypt(
                    eventobj.eventcontent.payload,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode()
                self.hand.append(card)
                if len(self.hand) == 5:
                    print("Carol's hand: ",end="")
                    for card in self.hand:
                        print(card[11:], end=" ")
                    print()

                header = GenericMessageHeader(PlayerMessageType.CONFIRM_HAND, 2, 0, interfaceid="0-2")
                message = GenericMessage(header, card)
                event = Event(self, EventTypes.MFRT, message)
                self.send_down(event)

#Construction of experiment with topology
