import time
import queue

from enum import Enum
from sys import byteorder
from ahc.Ahc import Event, EventTypes, ComponentModel
from Crypto.Cipher import DES
from ahc.MAC.GenericMAC import GenericMac, GenericMacEventTypes

class RipeMacEventTypes(Enum):
    HANDLE_MAC_FRAME = "HandleMacFrame"
    MAC_RESULT = "MacResult"

class RipeMac(ComponentModel):
    """RipeMac is the implementation of the RIPE-MAC algorithm in Ahc. It
    continuously expects events from bottom. The event
    content must be a `bytes` object which is the concatenation of the secret
    key (64 bits) and the message whose MAC will be generated. Once computed,
    the result will be sent back down with the event GenericMacEventTypes.MACRESULT."""

    def __init__(self, componentname, componentinstancenumber):
        ComponentModel.__init__(self, componentname, componentinstancenumber)
        self.framequeue = queue.Queue(maxsize=-1)
        self.eventhandlers[RipeMacEventTypes.HANDLE_MAC_FRAME] = self.handle_frame
    
    def on_init(self, eventobj: Event):
        self.send_self(
            Event(self, RipeMacEventTypes.HANDLE_MAC_FRAME, None)
        )  # Continuously trigger handle_frame

    def on_message_from_bottom(self, eventobj: Event):
        self.framequeue.put(eventobj)

    def handle_frame(self, eventobj: Event):
        if self.framequeue.qsize() > 0:
            try:
                # get event object and validate it
                eventobj: Event = self.framequeue.get()
                if not eventobj:
                    raise Exception("event retrieved from queue is None")
                if not isinstance(eventobj.eventcontent, bytes):
                    raise Exception(
                        "content of the event retrieved from queue is not bytes"
                    )
                if len(eventobj.eventcontent) <= 8:
                    raise Exception(
                        "content of the event must be 64-bit key concatenated with the message"
                    )

                # parse eventcontent into key and message
                key = eventobj.eventcontent[:8]
                message = eventobj.eventcontent[8:]

                # compute the mac value and send it back up
                mac = self._compute(key, message)
                self.send_down(Event(self, RipeMacEventTypes.MAC_RESULT, mac))
            except Exception as e:
                print("RipeMac handle_frame exception, ", e)

        time.sleep(0.1)
        self.send_self(Event(self, RipeMacEventTypes.HANDLE_MAC_FRAME, None))

    def _compute(self, key: bytes, message: bytes) -> bytes:
        """Executes the RIPE-MAC keyed hash function algoritm to obtain the MAC using
        the given key and message. Key must be 64-bit in length.
        #### Steps of the algorithm:
        - Expand the message to a multiple of 64 bits.
        - Split the message into 64-bit blocks.
        - Use a keyed-compression function to iteratively compress these blocks to a single block of 64 bits.
        - Finally, put this 64-bit block into a DES with a different key, derived from the main key.

        #### Compression Function:
        - Let m_i denote the ith 64-bit plaintext block.
        - Let h_i denote the result of the ith compression.
        - Initial value H_o is 0.
        - h_i = DES_k(m_i XOR h_{i-1}) XOR m_i

        #### Derived key:
        K' = K XOR 0xF0F0F0...F0
        """
        if len(key) != 8:
            raise Exception(f"Length of the key must be 64 bits, not {len(key) * 8}")
        if isinstance(message, str):
            message = message.encode()

        def xorBytes(b1: bytes, b2: bytes):
            """Returns the bitwise XOR of the given bytes. Their lengths must equal."""
            if len(b1) != len(b2):
                raise Exception("lengths of b1 and b2 must be equal")
            i1 = int.from_bytes(b1, byteorder)
            i2 = int.from_bytes(b2, byteorder)
            result = i1 ^ i2
            return result.to_bytes(len(b1), byteorder)

        # expand the message to a multiple of 64 bits
        expanded = message + b"\x00" * (8 - len(message) % 8)

        # split the message into 64-bit blocks
        blocks = list()
        i = 0
        while True:
            start = i * 8
            end = (i + 1) * 8
            block = expanded[start:end]
            if len(block) == 0:
                break
            blocks.append(block)
            i += 1

        # use a keyed-compression function to iteratively compress these blocks to a single block of 64 bits
        H = b"\x00" * 8  # IV is 00000000
        for block in blocks:
            desIn = xorBytes(block, H)
            desOut = DES.new(key, DES.MODE_ECB).encrypt(desIn)
            H = xorBytes(desOut, block)

        # finally, put this 64-bit block into a DES with a different key, derived from the main key
        KK = xorBytes(key, b"\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0")
        result = DES.new(KK, DES.MODE_ECB).encrypt(H)
        return result
