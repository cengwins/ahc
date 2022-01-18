from enum import Enum
from threading import Timer
import random
from ahc.Ahc import Topology, ComponentRegistry, ComponentModel, ConnectorTypes, Event, GenericMessageHeader, \
    GenericMessage, EventTypes
from ahc.Channels.Channels import Channel

registry = ComponentRegistry()
class ChandraMessageTypes(Enum):
    PRP = "propose"
    EST = "estimate"
    ACK = "acknowledge"
    NACK = "negacknowledge"
    DCD = "decide"
    IS_ALIVE = "iscoordinatoralive"

class ChandraPhases(Enum):
    IDLE = "idle"
    PRP_PHASE = "proposalphase"
    EST_PHASE = "estimatephase"
    ACK_PHASE = "ackphase"
    DCD_PHASE = "decisionphase"


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def selectCoordinator():
    cmp = get_coordinator()
    crdname = cmp.componentname
    crdinstancenumber = (cmp.componentinstancenumber + 1) % cmp.numberofNodes
    registry.get_component_by_key(crdname, crdinstancenumber).set_as_coordinator()
    cmp.set_as_proposer()

def start_next_round():
    print(f"No agreement. Next round coming up..")
    selectCoordinator()
    print(f"New coordinator is {get_coordinator().componentname}-{get_coordinator().componentinstancenumber}")
    cnodelist = list()
    for itemkey in registry.components:
        cmp = registry.components[itemkey]
        if cmp.componentname == "ChandraNode":
            cnodelist.append(cmp)
            #print(f"{cmp.componentname}-{cmp.componentinstancenumber}={type(cmp)}")
    for cmp in cnodelist:
        cmp.phase = ChandraPhases.IDLE
        cmp.faulty = random.randrange(100) > 95
        cmp.timer.cancel()
        cmp.timer = RepeatTimer(0.5, cmp.phase_handler)
        cmp.timer.start()
        cmp.start = True

def get_coordinator():
    cnodelist= list()
    for itemkey in registry.components:
        cmp = registry.components[itemkey]
        if cmp.componentname == "ChandraNode":
            cnodelist.append(cmp)

    for n in range(0,len(cnodelist)):
        if cnodelist[n].is_coordinator():
            return cnodelist[n]

class ChandraComponents(ComponentModel):
    def __init__(self, componentname, componentinstancenumber, numberofNodes):
        super().__init__(componentname, componentinstancenumber)
        self.phasehandlers = {ChandraPhases.IDLE: self.on_idle_phase, ChandraPhases.PRP_PHASE: self.on_proposal_phase,
                              ChandraPhases.EST_PHASE: self.on_estimate_phase,
                              ChandraPhases.ACK_PHASE: self.on_ACK_phase,
                              ChandraPhases.DCD_PHASE: self.on_decide_phase}
        self.numberofNodes = numberofNodes
        self.isCoordinator = False

        self.start = False
        self.phase = ChandraPhases.IDLE
        self.timer = RepeatTimer(0.5, self.phase_handler)
        self.count_ACK = 0
        self.count_proposal = 0

        self.value = random.randint(0, 3)
        self.timestamp = random.randint(0, 5)
        self.estimate = (self.value, self.timestamp)

        self.faulty = random.randrange(100) > 95 # Randomise faulty detection of coordinator



        print(f"Initial values for {self.componentname}-{self.componentinstancenumber} : "
              f"(Value,Timestamp)=({self.value},{self.timestamp})")

    def on_init(self, eventobj: Event):
        self.start = True
        self.timer.start()

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        msgtype = message.header.messagetype
        msgfrom = message.header.messagefrom

        messagePayload = message.payload
        value, timestamp = [int(n) for n in messagePayload.split("-")]

        if msgtype is ChandraMessageTypes.PRP:
            print(f"{msgfrom.componentname}-{msgfrom.componentinstancenumber} sent an proposal message to "
                  f"{self.componentname}-{self.componentinstancenumber} = ({value},{timestamp})")
            self.count_proposal = self.count_proposal + 1
            if timestamp > self.estimate[1]:
                self.estimate = (value, timestamp)

        elif msgtype is ChandraMessageTypes.EST:
            self.estimate = (value, timestamp)
            print(f"{msgfrom.componentname}-{msgfrom.componentinstancenumber} sent an estimate message to "
                  f"{self.componentname}-{self.componentinstancenumber} = ({value},{timestamp})")


        elif msgtype is ChandraMessageTypes.ACK:
            print(f"{msgfrom.componentname}-{msgfrom.componentinstancenumber} sent an ACK message to "
                  f"{self.componentname}-{self.componentinstancenumber}")
            self.count_ACK = self.count_ACK + 1

        elif msgtype is ChandraMessageTypes.NACK:
            print(f"{msgfrom.componentname}-{msgfrom.componentinstancenumber} sent an NACK message to "
                  f"{self.componentname}-{self.componentinstancenumber}")
            self.phase = ChandraPhases.IDLE
            start_next_round()

        # change the new value with the decision taken by coordinator
        elif msgtype is ChandraMessageTypes.DCD:
            self.value = value
            self.timestamp = timestamp
            print(f"Decision message is arrived. The new values and time stamps of the component "
                  f"{self.componentname}-{self.componentinstancenumber} = ({value},{timestamp})")

        elif msgtype is ChandraMessageTypes.FDI:
            # FailureDetector message
            pass

    def phase_handler(self):
        # print(f"{self.componentname}.{self.componentinstancenumber} previous phase is {self.phase}")
        self.phasehandlers[self.phase]()
        # print(f"{self.componentname}.{self.componentinstancenumber} next phase is {self.phase}")

    def on_idle_phase(self):
        if self.start:
            self.phase = ChandraPhases.PRP_PHASE
        else:
            self.timer.cancel()

    def on_proposal_phase(self):
        self.phase = ChandraPhases.EST_PHASE
        if not self.is_coordinator():
            self.send_propose_message()
        else:
            pass

    def on_estimate_phase(self):
        self.phase = ChandraPhases.ACK_PHASE
        if self.is_coordinator():
            if self.count_proposal >= (len(registry.components) + 1) / 2:
                print(f"The estimate of coordinator is: {self.estimate}")
                self.send_estimate_message()
            else:
                start_next_round()
        else:
            pass

    def on_ACK_phase(self):
        self.phase = ChandraPhases.DCD_PHASE
        if not self.is_coordinator():
            if not self.faulty:
                self.send_ACK()
            else:
                self.send_NACK()
        else:
            pass

    def on_decide_phase(self):
        self.phase = ChandraPhases.IDLE
        self.start = False
        if self.is_coordinator():
            if self.count_ACK >= (len(registry.components) + 1) / 2:
                self.send_decide_message()
            else:
                start_next_round()
        else:
            pass

    def send_propose_message(self):
        coordinator = get_coordinator()
        if self is not coordinator:
            cHeader = GenericMessageHeader(ChandraMessageTypes.PRP, self, coordinator)
            cPayload = f"{self.value}-{self.timestamp}"
            cEventContent = GenericMessage(cHeader, cPayload)
            cEvent = Event(self, EventTypes.MFRT, cEventContent)
            self.send_down(cEvent)
            self.send_self(cEvent)
        else:
            pass

    def send_estimate_message(self):
        coordinator = get_coordinator()
        if self is coordinator:
            cHeader = GenericMessageHeader(ChandraMessageTypes.EST, self, self.value, self.timestamp)
            cPayload = f"{self.estimate[0]}-{self.estimate[1]}"
            cEventContent = GenericMessage(cHeader, cPayload)
            cEvent = Event(self, EventTypes.MFRT, cEventContent)
            self.send_down(cEvent)
        else:
            pass

    def send_ACK(self):
        coordinator = get_coordinator()
        if self is not coordinator:
            cHeader = GenericMessageHeader(ChandraMessageTypes.ACK, self, coordinator)
            cPayload = f"{self.estimate[0]}-{self.estimate[1]}"
            cEventContent = GenericMessage(cHeader, cPayload)
            cEvent = Event(self, EventTypes.MFRT, cEventContent)
            self.send_down(cEvent)
        else:
            pass

    def send_NACK(self):
        coordinator = get_coordinator()
        if self is not coordinator:
            cHeader = GenericMessageHeader(ChandraMessageTypes.NACK, self, coordinator)
            cPayload = f"{self.estimate[0]}-{self.estimate[1]}"
            cEventContent = GenericMessage(cHeader, cPayload)
            cEvent = Event(self, EventTypes.MFRT, cEventContent)
            self.send_down(cEvent)
        else:
            pass

    def send_decide_message(self):
        coordinator = get_coordinator()
        if self is coordinator:
            cHeader = GenericMessageHeader(ChandraMessageTypes.DCD, self, None)
            cPayload = f"{self.estimate[0]}-{self.estimate[1]}"
            cEventContent = GenericMessage(cHeader, cPayload)
            cEvent = Event(self, EventTypes.MFRT, cEventContent)
            self.send_down(cEvent)
            self.value = self.estimate[0]
            self.timestamp = self.estimate[1]
            print(f"Agreement done. Change your values with decision: {cPayload}")
        else:
            pass

    def on_message_from_top(self, eventobj: Event):
        pass

    def set_as_coordinator(self):
        self.isCoordinator = True

    def set_as_proposer(self):
        self.isCoordinator = False
        self.count_ACK = 0
        self.count_proposal = 0

    def is_coordinator(self):
        return self.isCoordinator

class ChandraChannel(Channel):
  # Overwrite onDeliverToComponent if you want to do something in the last pipeline stage
  # onDeliver will deliver the message from the channel to the receiver component using messagefromchannel event
  def on_deliver_to_component(self, eventobj: Event):
    coordinator = get_coordinator()
    crdname = coordinator.componentinstancenumber
    callername = eventobj.eventsource.componentinstancenumber
    for item in self.connectors:
      callees = self.connectors[item]
      for callee in callees:
        calleename = callee.componentinstancenumber
        # print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
        if calleename == callername or (calleename!=crdname and callername !=crdname):
          pass
        else:
          myevent = Event(eventobj.eventsource, EventTypes.MFRB, eventobj.eventcontent, self.componentinstancenumber)
          callee.trigger_event(myevent)

class ChandraConsensusNode(ComponentModel):

    def __init__(self, componentname, componentid, numberofNodes=10):
        self.channel = ChandraChannel("ChandraChannel", 0)
        for n in range(0, numberofNodes):
            tComp = ChandraComponents("ChandraNode", n, numberofNodes)
            tComp.connect_me_to_channel(ConnectorTypes.DOWN, self.channel)
            registry.add_component(tComp)

        registry.get_component_by_key("ChandraNode", 0).set_as_coordinator()
        super().__init__(componentname, componentid)

def main():
    topo = Topology()
    topo.construct_single_node(ChandraConsensusNode, 0)
    topo.start()
    while True: pass


if __name__ == '__main__':
    main()
