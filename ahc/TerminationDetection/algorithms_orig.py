import queue
import random
from enum import Enum
from datetime import datetime as dt

from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from ahc.Ahc import (ComponentModel, Event, ConnectorTypes, ComponentRegistry, GenericMessagePayload, GenericMessageHeader,
                 GenericMessage, EventTypes)

registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageType(Enum):
    BASIC = "basic"
    CONTROL = "control"

class AHCNodeSimulationStatus(Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    OUT_OF_CLOCK = "ooc"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass

class ApplicationLayerComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber, context):
        super().__init__(componentname, componentinstancenumber, context=context)

        self.context = context
        # self.eventhandlers[ApplicationLayerMessageType.BASIC] = self.on_basic_message
        # self.eventhandlers[ApplicationLayerMessageType.CONTROL] = self.on_control_message

        self.basic_message_queue = queue.Queue(maxsize=-1)
        self.control_message_queue = queue.Queue(maxsize=-1)
        self.simulation_state = AHCNodeSimulationStatus.PASSIVE

        self.sleep_ms_per_tick = context["ms_per_tick"]
        self.simulation_ticks_total = context["simulation_ticks"]
        self.alive_for_next_ticks = context["initial_liveness"][componentinstancenumber]
        self.communication_on_active_prob = context["communication_on_active_prob"]
        self.min_activeness_after_receive = context["min_activeness_after_receive"]
        self.max_activeness_after_receive = context["max_activeness_after_receive"]
        self.package_process_per_tick = context["node_package_process_per_tick"]
        self.die_passiveness_threshold = context["passiveness_death_thresh"]

        if context["hard_stop_on_tick"] is None:
            self.hard_stop_on_tick = None
        else:
            self.hard_stop_on_tick = context["hard_stop_on_tick"][self.componentinstancenumber]

        self.friend_ids = [i for i in context["network"].G.nodes() if i != componentinstancenumber]

        self.__tick_n = 0
        self._passive_counter = 0

        if self.alive_for_next_ticks > 0:
            self.simulation_state = AHCNodeSimulationStatus.ACTIVE

    def prepare_application_layer_message(self, message_type: ApplicationLayerMessageType, destination_node_id: int, payload: object) -> GenericMessage:
        hdr = ApplicationLayerMessageHeader(message_type, self.componentinstancenumber, destination_node_id)
        payload = ApplicationLayerMessagePayload(payload)
        
        return GenericMessage(hdr, payload)

    def send_random_basic_message(self, to: int) -> None:
        self.send_down(Event(self, EventTypes.MFRT, self.prepare_application_layer_message(ApplicationLayerMessageType.BASIC, to, str(dt.now().timestamp()))))

    def on_init(self, eventobj: Event):
        # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_bottom(self, eventobj: Event):
        applmessage = eventobj.eventcontent
        hdr = applmessage.header

        # print(f"Node-{self.componentinstancenumber}: Node-{hdr.messagefrom} has sent {hdr.messagetype} message (payload: {applmessage.payload})")

        if hdr.messagetype == ApplicationLayerMessageType.BASIC:
            self.basic_message_queue.put_nowait(applmessage)
        elif hdr.messagetype == ApplicationLayerMessageType.CONTROL:
            self.control_message_queue.put_nowait(applmessage)

    def simulation_tick(self):
        next_state = None
        got_packages_from = None
        to_friend = None

        if self.__tick_n >= self.simulation_ticks_total:
            next_state = AHCNodeSimulationStatus.OUT_OF_CLOCK
        elif self._passive_counter >= self.die_passiveness_threshold:
            next_state = AHCNodeSimulationStatus.OUT_OF_CLOCK
        elif self.__tick_n >= self.hard_stop_on_tick:
            next_state = AHCNodeSimulationStatus.OUT_OF_CLOCK
            print(f"   ==> N-{self.componentinstancenumber}: HARD STOP")
        else:
            if self.simulation_state == AHCNodeSimulationStatus.OUT_OF_CLOCK:
                next_state = AHCNodeSimulationStatus.OUT_OF_CLOCK
            elif self.simulation_state == AHCNodeSimulationStatus.PASSIVE:
                if self.basic_message_queue.empty():
                    # no incoming package, still passive.
                    next_state = AHCNodeSimulationStatus.PASSIVE
                else:
                    got_packages_from = []

                    for _ in range(self.package_process_per_tick):
                        try:
                            package = self.basic_message_queue.get_nowait()
                            # print(f"+P+ N-{self.componentinstancenumber} <==BASIC== N-{package.header.messagefrom} ({package.payload.messagepayload})")
                            got_packages_from.append(package.header.messagefrom)
                        except queue.Empty:
                            break

                    self.alive_for_next_ticks = random.randint(self.min_activeness_after_receive, self.max_activeness_after_receive)
                    next_state = AHCNodeSimulationStatus.ACTIVE
            elif self.simulation_state == AHCNodeSimulationStatus.ACTIVE:
                got_packages_from = []

                for _ in range(self.package_process_per_tick):
                    try:
                        package = self.basic_message_queue.get_nowait()
                        # print(f"+A+ N-{self.componentinstancenumber} <==BASIC== N-{package.header.messagefrom} ({package.payload.messagepayload})")
                        got_packages_from.append(package.header.messagefrom)
                    except queue.Empty:
                        break

                if random.random() <= self.communication_on_active_prob:
                    # send package to a random friend..
                    to_friend = random.choice(self.friend_ids)
                    self.send_random_basic_message(to_friend)

                self.alive_for_next_ticks -= 1

                if self.alive_for_next_ticks == 0:
                    if len(got_packages_from) > 0:
                        # got a package, this means immeiate activeness from passive!
                        next_state = AHCNodeSimulationStatus.ACTIVE
                        self.alive_for_next_ticks = random.randint(self.min_activeness_after_receive, self.max_activeness_after_receive)
                    else:
                        next_state = AHCNodeSimulationStatus.PASSIVE
                else:
                    next_state = AHCNodeSimulationStatus.ACTIVE

        assert next_state is not None

        # ST: state
        # NS: next state
        # GPF: got packages from
        # SPF: sent package to friend
        # ANT: alive next ticks
        # P2P: packages to process
        # print(f"   ==> N-{self.componentinstancenumber}: ST: {self.simulation_state}, NS: {next_state}, GPF: {got_packages_from}, SPF: {to_friend}, ANT: {self.alive_for_next_ticks}, P2P: {self.basic_message_queue.qsize()}")

        # time.sleep(self.sleep_ms_per_tick / 1000)
        self.__tick_n += 1
        self.simulation_state = next_state

        if self.simulation_state == AHCNodeSimulationStatus.PASSIVE:
            self._passive_counter += 1
        elif self.simulation_state == AHCNodeSimulationStatus.ACTIVE:
            self._passive_counter = 0

        return next_state, to_friend

class AdHocNode(ComponentModel):
    def __init__(self, componentname, componentid, context):
        self.context = context
        # SUBCOMPONENTS
        self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid, context=self.context)
        self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

        super().__init__(componentname, componentid, context=self.context)

    def on_init(self, eventobj: Event):
        # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def simulation_tick(self):
        return self.appllayer.simulation_tick()

    @property
    def waiting_packages_on_queue(self):
        if self.appllayer.simulation_state == AHCNodeSimulationStatus.OUT_OF_CLOCK:
            return 0

        return self.appllayer.basic_message_queue.qsize()