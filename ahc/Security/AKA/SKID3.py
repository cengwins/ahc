"""
## SKID3 Protocol
This module contains the implementation of the SKID3 mutual authentication protocol.
It comprises of two peers, namely Alice and Bob and the RIPE-MAC algorithm which is
a keyed hash function. The protocol is carried out in the following steps:
- Alice chooses a random 64-bit number `Ra` and sends it to Bob.
- Bob receives `Ra`, chooses a 64-bit random number of its own `Rb` and send Alice
`Rb||B||Hk(Ra||Rb||B)` where `Hk()` is the RIPE-MAC function abd `B` is Bob's unique name.
- Alice receives Bob's response and recomputes `Hk(Ra||Rb||B)`. If received and recomputed
macs match, them Alice is said to have authenticated Bob. After this, Alice sends Bob
`A||Hk(Rb||A)` where `A` is Alice's unique name.
- Bob receives Alice's response and recomputes `Hk(Rb||A)`. If received and recomputed macs
match, then Bob is said to have authenticated Alice.

This protocol is based on the assumption that both Alice and Bob share a secret key
which only they know and is used when creating the MACs.

### Implementation
- Alice and Bob are connected to each other as peers.
- Both Alice and Bob are connected to a RIPE-MAC component which is above them
"""

from enum import Enum
from sys import byteorder
from random import randint

from ahc.Ahc import ComponentModel, Event, EventTypes
from ahc.MAC.RipeMAC import RipeMacEventTypes


class SKID3EventTypes(Enum):
    UNAUTHENTICATED = "UNAUTHENTICATED"     # The event that is triggered when one side receives a wrong response to the challange it had sent.

class SKID3(ComponentModel):
    class State(Enum):
        INITIAL = "Initial"
        STEP1 = "Step1"
        STEP2 = "Step2"
        STEP3 = "Step3"
        SUCCESS = "Success"
        FAIL = "Fail"
        
        def __str__(self):
            return str(self.value)

    def __init__(
        self,
        componentname,
        componentinstancenumber,
        secretKey: bytes,
        context=None,
        configurationparameters=None,
        num_worker_threads=1,
    ):
        super().__init__(
            componentname,
            componentinstancenumber,
            context=context,
            configurationparameters=configurationparameters,
            num_worker_threads=num_worker_threads,
        )

        self.secretKey = secretKey
        self.eventhandlers[SKID3EventTypes.UNAUTHENTICATED] = self.onReceiveUnauthenticated

    def setState(self, state: State):
        self.state = state
        # print(f"{self.componentname} got to state '{state}'")
        if state in [SKID3.State.FAIL, SKID3.State.SUCCESS]:
            self.terminate()
            exit(0)            

    def getRandomInt64(self):
        return randint(0, 0x7FFFFFFFFFFFFFFF)

    def int64ToBytes(self, number: int):
        return number.to_bytes(8, "little", signed=True)

    def int64FromBytes(self, b: bytes, start: int = 0):
        if len(b) < 8 + start:
            raise Exception("To extract int64, bytes needs to be larger than 7 bytes")

        return int.from_bytes(b[start : start + 8], "little", signed=True)

    def getStringFromBytes(self, b: bytes, start: int = 0):
        """Extracts a string that ends with '\0' from b, with the starting offset as start parameter."""
        end = b.find(0)
        if end < 0:
            raise Exception(
                "Cannot extract string from bytes because '\0' character wasn't found"
            )

        return b[start:end]

    def getMacFromBytes(self, b: bytes, start: int = 0):
        """Extracts a RIPE-MAC result from the given bytes."""
        n = 64  # the length of the RIPE-MAC output
        return b[start : start + n]

    def sendMacEvent(self, *messages):
        content = self.secretKey
        for m in messages:
            if isinstance(m, bytes):
                content = content + m
            elif isinstance(m, str):
                content = content + m.encode()
            elif isinstance(m, int):
                content = content + m.to_bytes(8, byteorder)

        self.send_up(Event(self, EventTypes.MFRB, content))

    def onMacResult(self, eventobj: Event):
        print(f"SKID3.onMacResult: got an unhandled MACRESULT event")
    
    def onReceiveUnauthenticated(self, eventobj: Event):
        self.setState(SKID3.State.FAIL)


class Alice(SKID3):
    def __init__(
        self,
        componentname,
        componentinstancenumber,
        context=None,
        configurationparameters=None,
        num_worker_threads=1,
        secretKey=None,
    ):
        super().__init__(
            componentname,
            componentinstancenumber,
            context=context,
            configurationparameters=configurationparameters,
            num_worker_threads=num_worker_threads,
            secretKey=secretKey,
        )
        self.state = SKID3.State.INITIAL
        self.eventhandlers[RipeMacEventTypes.MAC_RESULT] = self.onMacResult
    

    def onMacResult(self, eventobj: Event):
        if eventobj.eventcontent is None or not isinstance(
            eventobj.eventcontent, bytes
        ):
            print(f"{self.unique_name()}: invalid MAC result event")
            return

        if self.state == SKID3.State.STEP2:
            # having received `Rb, B, Hk(Ra, Rb, B)` from Bob, compare the MACs
            if self.BobMac != eventobj.eventcontent:
                self.send_peer(Event(self, SKID3EventTypes.UNAUTHENTICATED, None))
                self.setState(SKID3.State.FAIL)
                return

            # now, compute `Hk(Rb, A)`
            self.sendMacEvent(self.Rb, self.unique_name())
            self.setState(SKID3.State.STEP3)

        elif self.state == SKID3.State.STEP3:
            # send `A, Hk(Rb, A)` to Bob
            data = self.unique_name().encode() + b'\0' + eventobj.eventcontent
            event = Event(self, EventTypes.MFRP, data)
            self.send_peer(event)
            self.setState(SKID3.State.SUCCESS)

    def on_init(self, eventobj: Event):
        if self.state != SKID3.State.INITIAL:
            return

        # Choose random 64-bit number `Ra` and send it to Bob
        self.Ra = self.getRandomInt64()
        self.send_peer(Event(self, EventTypes.MFRP, self.int64ToBytes(self.Ra)))
        self.setState(SKID3.State.STEP1)

    def on_message_from_peer(self, eventobj: Event):
        if eventobj is None or not isinstance(eventobj.eventcontent, bytes):
            print(f"{self.unique_name()}: got invalid message from bottom")
            return

        if self.state == SKID3.State.STEP1:
            # Bob has sent `( Rb, B, Hk(Ra, Rb, B) )`
            self.Rb = self.int64FromBytes(eventobj.eventcontent)
            self.BobName = self.getStringFromBytes(eventobj.eventcontent, 8)
            self.BobMac = self.getMacFromBytes(
                eventobj.eventcontent, 8 + len(self.BobName) + 1
            )

            # now, recompute Hk(Ra, Rb, B)
            self.sendMacEvent(self.Ra, self.Rb, self.BobName)
            self.setState(SKID3.State.STEP2)


class Bob(SKID3):
    def __init__(
        self,
        componentname,
        componentinstancenumber,
        context=None,
        configurationparameters=None,
        num_worker_threads=1,
        secretKey=None,
    ):
        super().__init__(
            componentname,
            componentinstancenumber,
            context=context,
            configurationparameters=configurationparameters,
            num_worker_threads=num_worker_threads,
            secretKey=secretKey,
        )
        self.state = SKID3.State.INITIAL
        self.eventhandlers[RipeMacEventTypes.MAC_RESULT] = self.onMacResult

    def onMacResult(self, eventobj: Event):
        if eventobj.eventcontent is None or not isinstance(
            eventobj.eventcontent, bytes
        ):
            print(f"{self.unique_name()}: invalid MAC result event")
            return

        if self.state == SKID3.State.STEP1:
            # having received `Ra`` from Alice, send back `Rb, B, Hk(Ra, Rb, B)`
            data = (
                self.int64ToBytes(self.Rb) + self.unique_name().encode() + b'\0' + eventobj.eventcontent
            )
            event = Event(self, EventTypes.MFRP, data)
            self.send_peer(event)
            self.setState(SKID3.State.STEP2)
        elif self.state == SKID3.State.STEP3:
            # having received `Hk(Rb, A)` from Alice and recomputed it, compare them
            if self.AliceMac != eventobj.eventcontent:
                self.send_peer(Event(self, SKID3EventTypes.UNAUTHENTICATED, None))
                self.setState(SKID3.State.FAIL)
                return
            self.setState(SKID3.State.SUCCESS)

    def on_message_from_peer(self, eventobj: Event):
        if eventobj is None or not isinstance(eventobj.eventcontent, bytes):
            print(f"{self.unique_name()}: got invalid message from bottom")
            return

        if self.state == SKID3.State.INITIAL:
            # Alice sent `Ra`, select random 64-bit int `Rb`
            self.Ra = self.int64FromBytes(eventobj.eventcontent)
            self.Rb = self.getRandomInt64()
            self.sendMacEvent(self.Ra, self.Rb, self.unique_name())
            self.setState(SKID3.State.STEP1)
        elif self.state == SKID3.State.STEP2:
            # Alice sent `A, Hk(Rb, A)`
            self.AliceName = self.getStringFromBytes(eventobj.eventcontent)
            self.AliceMac = self.getMacFromBytes(
                eventobj.eventcontent, len(self.AliceName) + 1
            )

            # send MAC event to recompute `Hk(Rb, A)`
            self.sendMacEvent(self.Rb, self.AliceName)
            self.setState(SKID3.State.STEP3)
