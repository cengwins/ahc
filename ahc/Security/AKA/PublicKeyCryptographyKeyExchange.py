""" Implementation of Key Exchange with Public-Key Cryptography as described in
    Schneier, Bruce (2007) Applied Cryptography: Protocols, Algorithms and
    Source Code in C, 20th Anniversary Edition
    From Chapter 3.1: Key Exchange
    This protocol is insecure and should not be used in production.
    See Chapter 3.1 of the book for more details about possible MITM attack.
    This implementation is used for demonstration purposes only.
"""

__author__ = "Goksel Kabadayi"
__contact__ = "gokselkabadayi@gmail.com"
__copyright__ = "Copyright 2022, WINSLAB"
__credits__ = ["Goksel Kabadayi"]
__date__ = "2022-01-15"
__deprecated__ = False
__email__ = "gokselkabadayi@gmail.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature


from ahc.Ahc import ComponentModel, GenericMessage, GenericMessageHeader, GenericMessagePayload, Event, EventTypes


class KDCRequestMessage(GenericMessage):
    pass


class KDCRequestMessageHeader(GenericMessageHeader):
    pass


class KDCRequestMessagePayload(GenericMessagePayload):
    pass


class KDCResponseMessage(GenericMessage):
    pass


class KDCResponseMessageHeader(GenericMessageHeader):
    pass


class KDCResponseMessagePayload(GenericMessagePayload):
    pass


class EncryptedMessage(GenericMessage):
    pass


class EncryptedMessageHeader(GenericMessageHeader):
    pass


class EncryptedMessagePayload(GenericMessagePayload):
    pass


class KDC(ComponentModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_public_keys = {}  # type: dict[str, rsa.RSAPublicKey]

        # Private key for signing responses
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        # Public key of KDC for clients to trust
        self.public_key = self.private_key.public_key()

    """Gets KDC's public key.
    Used by Alice to verify signature of the response."""

    def get_public_key(self) -> rsa.RSAPublicKey:
        return self.public_key

    """Registers a public key to make it available to clients.
    Bob's public key is registered using this method.
    Registration is done while nodes are initializing."""

    def register_public_key(self, client_name: str, public_key: rsa.RSAPublicKey):
        self.client_public_keys[client_name] = public_key

    """Gets triggered when Alice requests a public key.
    Signs and sends Bob's public key to Alice."""

    def on_message_from_bottom(self, eventobj: Event):
        name = eventobj.eventcontent.payload.messagepayload
        public_key = self.client_public_keys.get(name)
        signature = self.private_key.sign(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        msg = KDCResponseMessage(
            KDCResponseMessageHeader(
                "response",
                self.componentinstancenumber,
                0
            ),
            KDCResponseMessagePayload(
                (public_key, signature)
            )
        )
        evt = Event(self, EventTypes.MFRT, msg)
        self.send_down(evt)
        print("[1] KDC sent response to Alice.")


class Alice(ComponentModel):
    """Saves KDC's trusted public key in this instance
    Used to verify the signature of KDC's response."""

    def set_kdc_public_key(self, public_key: rsa.RSAPublicKey):
        self.kdc_public_key = public_key

    def on_init(self, eventobj: Event):
        msg = KDCRequestMessage(
            KDCRequestMessageHeader(
                "request",
                self.componentinstancenumber,
                0
            ),
            KDCRequestMessagePayload(
                "Bob"
            )
        )
        evt = Event(self, EventTypes.MFRT, msg)
        self.send_down(evt)
        print("[1] Alice asked KDC for Bob's public key.")

    """Gets triggered when KDC sends a response to Alice.
    Alice verifies the signature of the response and
    uses the public key to encrypt session key
    and sends it to Bob."""

    def on_message_from_bottom(self, eventobj: Event):
        response_content = eventobj.eventcontent.payload.messagepayload
        public_key = response_content[0]  # type: rsa.RSAPublicKey
        signature = response_content[1]  # type: bytes
        try:
            # Verify signature of KDC's response
            self.kdc_public_key.verify(
                signature,
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except InvalidSignature:
            # KDC's signature does not match with stored public key
            # Message is either corrupted or tampered with.
            raise Exception("Invalid KDC signature.")

        # KDC's signature matches with stored public key.
        print("[1] Alice got Bob's public key from KDC.")

        # Generate session key
        self.session_key = Fernet.generate_key()

        print("[2] Alice generated random session key: {}".format(self.session_key))

        # Encrypt session key with Bob's public key
        encrypted_session_key = public_key.encrypt(
            self.session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        print("[2] Alice encrypted random session key using Bob's public key.")
        # Encapsulate encrypted session key in EncryptedMessage
        msg = EncryptedMessage(
            EncryptedMessageHeader(
                "encrypted",
                self.componentinstancenumber,
                0
            ),
            EncryptedMessagePayload(
                encrypted_session_key
            )
        )
        # Send message to Bob
        evt = Event(self, EventTypes.MFRT, msg)
        self.send_up(evt)
        print("[2] Alice sent encrypted session key to Bob.")


class Bob(ComponentModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create key pair
        # Public key is registered to KDC
        # Private key is used to decrypt incoming messages
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        self.session_key = None

    """Gets public key of this instance.
    Used to register this instance's public key to KDC"""

    def get_public_key(self) -> rsa.RSAPublicKey:
        return self.public_key

    """Gets triggered when Alice sends an encrypted session key to Bob.
    Bob decrypts the session key and saves it in this instance.
    If Bob receives correct session key, Alice and Bob can encrypt their
    communications using this key."""

    def on_message_from_bottom(self, eventobj: Event):
        encrypted_session_key = eventobj.eventcontent.payload.messagepayload
        self.session_key = self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        print("[3] Bob decrypted random session key using his private key.")
        print("Bob's session key: {}".format(self.session_key))
