from enum import IntEnum, auto
from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader
from Ahc import EventTypes
from collections import defaultdict


class ChandyLamportMessageTypes(IntEnum):
    MARK = auto()
    GSU = auto()


class ChandyLamportComponentModel(ComponentModel):
    """A ComponentModel that you can take a snapshot of using the
    Chandy-Lamport algorithm"""

    def channel_of(self, eventobj: Event):
        from_chnl = eventobj.fromchannel
        if from_chnl is None:
            raise Exception(f"Received {ChandyLamportEventTypes.MARK} from a "
                            "non-channel component")

        return from_chnl

    def gsu_recv(self, recv_state, from_chnl):
        self.global_state |= recv_state
        self.gsu_chnls.add(from_chnl)
        if self.gsu_chnls != self.in_chnls:
            return

        self.gsu_chnls.clear()
        if not self.init_snapshot:
            return

        print(f"Reporting snapshot result:")
        for comp, state in self.global_state.items():
            print(f"State of: {comp}:")
            for i in range(len(state)):
                print(f"  {i}: {state[i].event}")

        self.init_snapshot = False


    def broadcast(self, event: Event):
        self.send_down(event)
        self.send_peer(event)
        self.send_up(event)

    def mark_send(self):
        self.state = list(self.inputqueue.queue)
        mark_msg = GenericMessage(
            GenericMessageHeader(ChandyLamportMessageTypes.MARK, None, None),
            None)
        self.broadcast(Event(self, EventTypes.MFRT, mark_msg))

    def report_snapshot(self):
        """Initializes a global snapshot and a report will be printed out when
        complete"""
        self.init_snapshot = True
        self.mark_send()

    def mark_recv(self, from_chnl):
        print(f"MARK recevied from channel: {from_chnl}")
        if self.state is None:
            self.mark_send()
            self.in_chnl_states[from_chnl] = []
        else:
            self.in_chnl_states[from_chnl] = self.in_chnl_events[from_chnl]

        self.mark_recv_chnls.add(from_chnl)
        if self.mark_recv_chnls == self.in_chnls:
            # Local snapshot completed, broadcast and reset the local state
            local_state = { self.unique_name(): self.state }
            for c, s in self.in_chnl_states.items():
                local_state[str(c)] = s

            self.global_state |= local_state
            gsu_msg = GenericMessage(
                GenericMessageHeader(ChandyLamportMessageTypes.GSU, None, None),
                self.global_state)
            self.broadcast(Event(self, EventTypes.MFRT, gsu_msg))
            self.reset_state()


    def msg_recv(self, event: Event):
        from_chnl = self.channel_of(event)
        # If received message is of type MARK or GSU; process them separately
        if type(contnt := event.eventcontent) == GenericMessage and\
           type(header := contnt.header) == GenericMessageHeader:
            if header.messagetype == ChandyLamportMessageTypes.MARK:
                self.mark_recv(from_chnl)
                return

            if header.messagetype == ChandyLamportMessageTypes.GSU:
                self.gsu_recv(contnt.payload, from_chnl)
                return

        if self.state is None:
            return

        # If the state is not recorded
        if from_chnl not in self.in_chnl_states:
            self.in_chnl_events[from_chnl].append(event)

    # When overridden call this function with 'super'
    def on_message_from_bottom(self, eventobj: Event):
        return self.msg_recv(eventobj)

    # When overridden call this function with 'super'
    def on_message_from_peer(self, eventobj: Event):
        return self.msg_recv(eventobj)

    # When overridden call this function with 'super'
    def on_message_from_top(self, eventobj: Event):
        return self.msg_recv(eventobj)

    def on_connected_to_channel(self, name, channel):
        super().on_connected_to_channel(name, channel)
        self.in_chnls.add(channel.componentinstancenumber)


    def connect_me_to_component(self, name, component):
        raise Exception(f"Only channels are allowed for connection to"
                        " {self.__class__}")


    def reset_state(self):
        self.state = None
        self.in_chnl_states.clear()
        self.in_chnl_events.clear()
        self.mark_recv_chnls.clear()

    def __init__(self, componentname, componentinstancenumber,
                     num_worker_threads=1):
        super().__init__(componentname, componentinstancenumber,
                         num_worker_threads=num_worker_threads)
        self.state = None
        self.global_state = dict()
        self.in_chnl_states = dict()
        self.in_chnl_events = defaultdict(list)
        self.mark_recv_chnls = set()
        self.in_chnls = set()
        self.init_snapshot = False
        self.gsu_chnls = set()
