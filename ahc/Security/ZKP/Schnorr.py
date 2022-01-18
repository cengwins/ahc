from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Channels.Channels import Channel
from enum import IntEnum
from random import randint
from Crypto.PublicKey import DSA

registry = ComponentRegistry()

KEY_LENGTH = 1024
CHALLENGE_LEVEL = 512

class ProverState(IntEnum):
    INITIAL = 0
    WAITFORDOMAINACCEPTED = 1
    WAITFORCHALLENGE = 2
    WAITFORVERIFIED = 3
    DONE = 4

class VerifierState(IntEnum):
    INITIAL = 0
    WAITFORDOMAIN = 1
    WAITFORRANDOM = 2
    WAITFORCHECKER = 3
    DONE = 4

class Prover(ComponentModel):

    state = None
    key = None
    p = None
    q = None
    g = None
    v = None
    s = None
    r = None
    e = None
    y = None
    x = None

    def __init__(self, componentname, componentid):
        self.state = ProverState.INITIAL
        self.key = DSA.generate(KEY_LENGTH)
        self.p = self.key.p
        self.q = self.key.q
        self.g = self.key.g
        self.v = self.key.y
        self.s = self.key.x
        super().__init__(componentname, componentid)

    def on_init(self, eventobj: Event):
        print("Prover -> Verifier : Sending domain. : ", [self.p, self.q, self.g, self.v])
        self.state = ProverState.WAITFORDOMAINACCEPTED
        self.send_down(Event(self, EventTypes.MFRT, [self.p, self.q, self.g, self.v]))
        

    def on_message_from_bottom(self, eventobj: Event):
        if self.state == ProverState.INITIAL:
            pass
        elif self.state == ProverState.WAITFORDOMAINACCEPTED:
            if eventobj.eventcontent == "SUCCESS":
                self.r = randint(1,self.q)
                self.x = pow(self.g, self.r, self.p)
                print("Prover -> Verifier : Sending random. : ", self.x)
                self.state = ProverState.WAITFORCHALLENGE
                self.send_down(Event(self, EventTypes.MFRT, self.x))
                
        elif self.state == ProverState.WAITFORCHALLENGE:
            self.e = eventobj.eventcontent
            self.y = (self.r + self.s * self.e) % self.q
            print("Prover -> Verifier : Sending checker. : ", self.y)
            self.state = ProverState.WAITFORVERIFIED
            self.send_down(Event(self, EventTypes.MFRT, self.y))

        elif self.state == ProverState.WAITFORVERIFIED:
            if eventobj.eventcontent == "DONE":
                self.state = ProverState.DONE
        
        


class Verifier(ComponentModel):

    state = None
    p = None
    q = None
    g = None
    v = None
    x = None
    e = None
    y = None

    def __init__(self, componentname, componentid):
        self.state = VerifierState.INITIAL
        super().__init__(componentname, componentid)

    def on_init(self, eventobj: Event):
        self.state = VerifierState.WAITFORDOMAIN

    def on_message_from_bottom(self, eventobj: Event):
        if self.state == VerifierState.WAITFORDOMAIN:
            self.p = eventobj.eventcontent[0]
            self.q = eventobj.eventcontent[1]
            self.g = eventobj.eventcontent[2]
            self.v = eventobj.eventcontent[3]
            print("Verifier -> Prover : Sending success.")
            self.state = VerifierState.WAITFORRANDOM
            self.send_down(Event(self, EventTypes.MFRT, "SUCCESS"))
            
        elif self.state == VerifierState.WAITFORRANDOM:
            self.x = eventobj.eventcontent
            self.e = randint(1,pow(2, CHALLENGE_LEVEL))
            print("Verifier -> Prover : Sending challenge. : ", self.e)
            self.state = VerifierState.WAITFORCHECKER
            self.send_down(Event(self, EventTypes.MFRT, self.e))
            
        elif self.state == VerifierState.WAITFORCHECKER:
            self.y = eventobj.eventcontent
            a = pow(self.g, self.y, self.p)
            b = pow(self.v, -self.e, self.p)
            expression = self.x == (a * b) % self.p
            if expression == True:
                print("Prover succeed.")
            else:
                print("Prover failed.")
            print("Verifier -> Prover : Sending done.")
            self.state == VerifierState.DONE
            self.send_down(Event(self, EventTypes.MFRT, "DONE"))
            
