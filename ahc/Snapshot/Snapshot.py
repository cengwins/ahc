from enum import Enum
from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader
from ahc.Ahc import EventTypes
from collections import defaultdict

class SnapshotEventTypes(Enum):
    # Take snapshot event
    TS = "TS"

class SnapshotMessageTypes(Enum):
    GSU = "GSU"


class SnapshotComponentModel(ComponentModel):

    def __init__(self, componentname, componentinstancenumber,
                 num_worker_threads=1):
        super().__init__(componentname, componentinstancenumber,
                         num_worker_threads=num_worker_threads)
        self.state = None
        self.gsu_redirected_comps = set()
        self.recv_events = []
        self.chnls = set()
        self.init_snapshot = False
        self.eventhandlers[SnapshotEventTypes.TS] = self.take_snapshot

    def connect_me_to_component(self, name, component):
        raise Exception(f"Only channels are allowed for connection to"
                        " {self.__class__}")

    def on_connected_to_channel(self, name, channel):
        super().on_connected_to_channel(name, channel)
        self.chnls.add(channel.componentinstancenumber)

    def channel_of(self, eventobj: Event):
        from_chnl = eventobj.fromchannel
        if from_chnl is None:
            raise Exception(f"Received a message from a non-channel component")

        return from_chnl

    def on_pre_event(self, event):
        return self.recv_events.append(event)

    def msg_recv(self, event: Event):
        """Generic message received function"""
        pass

    def send_msg(self, event: Event):
        pass

    def send_gsu(self, local_state):
        gsu_msg = GenericMessage(
            GenericMessageHeader(SnapshotMessageTypes.GSU, None, None),
            local_state)
        self.send_msg(Event(self, EventTypes.MFRT, gsu_msg))

    def gsu_recv(self, state):
        # Redirect the GSU if we are not the source component of the snapshot
        if state.component_id not in self.gsu_redirected_comps:
            self.gsu_redirected_comps.add(state.component_id)
            self.send_gsu(state)

        self.on_gsu_recv(state)

    def on_gsu_recv(self, state):
        pass

    def on_take_snapshot(self):
        """Generic report snapshot"""
        pass

    def take_snapshot(self, eventobj: Event):
        self.init_snapshot = True
        self.on_take_snapshot()

    # When overridden call this function with 'super'
    def on_message_from_bottom(self, eventobj: Event):
        return self.msg_recv(eventobj)

    # When overridden call this function with 'super'
    def on_message_from_peer(self, eventobj: Event):
        return self.msg_recv(eventobj)

    # When overridden call this function with 'super'
    def on_message_from_top(self, eventobj: Event):
        return self.msg_recv(eventobj)

    def reset_state(self):
        self.state = None
        self.gsu_redirected_comps.clear()

class ChandyLamportMessageTypes(Enum):
    MARK = "MARK"


class ChandyLamportState:
    def __init__(self, component, state, chnl_states):
        self.component_id = component
        self.component_state = []
        for s in state:
            self.component_state.append(s)

        self.chnl_states = defaultdict(list)
        for c, s in chnl_states.items():
            self.chnl_states[c].append(s)

class ChandyLamportComponentModel(SnapshotComponentModel):
    """A ComponentModel that you can take a snapshot of using the
    Chandy-Lamport algorithm"""

    def __init__(self, componentname, componentinstancenumber,
                     num_worker_threads=1):
        super().__init__(componentname, componentinstancenumber,
                         num_worker_threads=num_worker_threads)
        self.global_state = dict()
        self.in_chnl_states = defaultdict(list)
        self.in_chnl_events = defaultdict(list)
        self.mark_recv_chnls = set()
        self.gsu_chnls = set()

    def on_gsu_recv(self, state: ChandyLamportState):
        if not self.init_snapshot:
            return

        report=f"State of component: {state.component_id}="
        report += ", ".join(str(e) for e in state.component_state)
        print(report)
        for chnl, events in state.chnl_states.items():
            chnl_rep = f"State of channel: {chnl}="
            chnl_rep += ", ".join(str(e) for e in events)
            print(chnl_rep)

    def send_msg(self, event: Event):
        self.send_down(event)

    def mark_send(self):
        # Record the state
        self.state = []
        for re in self.recv_events:
            self.state.append(re)

        # Broadcast the mark message
        mark_msg = GenericMessage(
            GenericMessageHeader(ChandyLamportMessageTypes.MARK, None, None),
            None)
        self.send_msg(Event(self, EventTypes.MFRT, mark_msg))

    def on_take_snapshot(self):
        """Initializes a global snapshot and a report will be printed out when
        complete"""
        self.mark_send()

    def mark_recv(self, from_chnl):
        if self.state is None:
            # First mark message, save component and channel state
            self.mark_send()
            self.in_chnl_states[from_chnl] = []
        else:
            # Consequent mark messages, save channel states
            for e in self.in_chnl_events[from_chnl]:
                self.in_chnl_states[e].append(e)

        self.mark_recv_chnls.add(from_chnl)
        if self.mark_recv_chnls == self.chnls:
            # Local snapshot completed, broadcast the local state
            local_state = ChandyLamportState(self.componentinstancenumber,
                                             self.state, self.in_chnl_states)
            gsu_msg = GenericMessage(
                GenericMessageHeader(SnapshotMessageTypes.GSU, None, None),
                local_state)
            self.send_msg(Event(self, EventTypes.MFRT, gsu_msg))
            self.gsu_recv(local_state)

    def msg_recv(self, event: Event):
        from_chnl = self.channel_of(event)
        # If received message is of type MARK or GSU; process them separately
        if type(contnt := event.eventcontent) == GenericMessage and\
           type(header := contnt.header) == GenericMessageHeader:
            if header.messagetype == ChandyLamportMessageTypes.MARK:
                self.mark_recv(from_chnl)
            elif header.messagetype == SnapshotMessageTypes.GSU:
                self.gsu_recv(contnt.payload)

            return event

        if self.state is None:
            return event

        # If the state is not recorded
        if from_chnl not in self.in_chnl_states:
            self.in_chnl_events[from_chnl].append(event)

        return event

    def reset_state(self):
        super().reset_state()
        self.in_chnl_states.clear()
        self.in_chnl_events.clear()
        self.mark_recv_chnls.clear()


class LaiYangState:
    def __init__(self, comp_id, comp_state, received, sent):
        self.component_id = comp_id
        self.component_state = []
        for cs in comp_state:
            self.component_state.append(cs)

        self.received = defaultdict(list)
        for chnl, r in received.items():
            self.received[chnl].append(r)

        self.sent = defaultdict(list)
        for chnl, s in sent.items():
            self.sent[chnl].append(s)

class LaiYangComponentModel(SnapshotComponentModel):
    def __init__(self, componentname, componentinstancenumber,
                 num_worker_threads=1):
        super().__init__(componentname, componentinstancenumber,
                         num_worker_threads=num_worker_threads)
        self.chnl_recv = defaultdict(list)
        self.chnl_sent = defaultdict(list)
        self.global_state = dict()
        self.sent_remaining = dict()
        self.recv_remaining = dict()

    def send_msg(self, event: Event):
        event.eventcontent = (event.eventcontent, self.state is not None)
        for c in self.chnls:
            self.chnl_sent[c].append(event)

        self.send_down(event)

    def handle_snapshot(self):
        # Take a snapshot
        self.state = LaiYangState(self.componentinstancenumber,
                                  self.recv_events, self.chnl_recv,
                                  self.chnl_sent)
        self.gsu_recv(self.state)

    def on_take_snapshot(self):
        self.handle_snapshot()

        # Broadcast a dummy message so that other components record
        # and broadcast their snapshots
        self.send_msg(Event(self, EventTypes.MFRT, "dummy"))

    def report_and_save_channel_state(self, channel, set_recv, set_sent):
        if not set_recv.issubset(set_sent):
            raise Exception("Not a consistent global state")

        chnl_state = list(set_sent - set_recv)
        self.global_state[channel] = chnl_state
        print(f"State of channel: {channel}=chnl_state")

    def on_gsu_recv(self, state: LaiYangState):
        if not self.init_snapshot:
            return
        # Report the snapshot if we are the source component of the snapshot
        self.global_state[state.component_id] = state.component_state
        report = f"State of component: {state.component_id}="
        report += ", ".join(str(e) for e in state.component_state)
        print(report)

        # Compute the messages in transit
        for chnl, recv in state.received:
            if chnl in self.sent_remaining:
                self.report_and_save_channel_state(
                    chnl, set(recv), set(self.sent_remaining[chnl]))
            else:
                self.recv_remaining[chnl] = recv

        for chnl, sent in state.sent:
            if chnl in self.recv_remaining:
                self.report_and_save_channel_state(
                    chnl, set(self.recv_remaining[chnl]), set(sent))
            else:
                self.sent_remaining[chnl] = sent

    def msg_recv(self, event: Event):
        content = event.eventcontent
        if type(content) is not tuple or len(content) != 2:
            raise Exception("Malformed message received by: "
                            "{self.unique_name()}")

        # Unpack the event content and modify the event with the actual content
        act_cntnt, post_snapshot = content
        event.eventcontent = act_cntnt

        # We are white and the message is post-snapshot
        if self.state is None and post_snapshot:
            self.handle_snapshot()

        from_chnl = self.channel_of(event)
        self.chnl_recv[from_chnl].append(event)

        # If not a GSU message return the modified event
        if type(act_cntnt) != GenericMessage or\
           type(header := act_cntnt.header) != GenericMessageHeader or\
               header.messagetype != SnapshotMessageTypes.GSU:
            return event

        self.gsu_recv(act_cntnt.payload)
        return event

    def reset_state(self):
        super().reset_state()
        self.global_state.clear()
