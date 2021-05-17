import sys

from Ahc import ComponentModel, EventTypes, ConnectorTypes
from Ahc import Event

from Consensus.Raft.states import Follower
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


class RaftConsensusComponent(ComponentModel):

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber, 1)
        self.state = None

    def on_message_from_bottom(self, eventobj: Event):
        self.data_received_peer(eventobj.eventsource, eventobj.eventcontent)

    def on_message_from_top(self, eventobj: Event):
        print("client asking for a trouble...")
        self.data_received_client(eventobj.eventsource, eventobj.eventcontent)

    def change_state(self, new_state):
        self.state.teardown()
        logger.info('For component %s State change:' + new_state.__name__, self.componentinstancenumber)
        self.state = new_state(old_state=self.state)

    def data_received_peer(self, sender, message):
        self.state.data_received_peer(sender, message)

    def data_received_client(self, client, message):
        self.state.data_received_client(client, message)

    def send(self, client, message):
        client.send(message)

    def send_to_component(self, recipient, message):
        if recipient != self:
            for conn in self.connectors[ConnectorTypes.DOWN]:
                if conn.componentinstancenumber.find(recipient.componentinstancenumber) != -1:
                    conn.trigger_event(Event(self, EventTypes.MFRT, message))

    def broadcast_peers(self, message):
        self.send_down(Event(self, EventTypes.MFRT, message))

    def on_init(self, eventobj: Event):
        self.state = Follower(server=self)


class ConsensusComponent(ComponentModel):

    def __init__(self, component_name, component_id):
        super().__init__(component_name, component_id, 1)
        self._commitIndex = 0
        self._currentTerm = 0
        self._lastApplied = 0
        self._lastLogIndex = 0
        self._lastLogTerm = None
        self._state = Follower()
        self._log = []

    def set_log(self, log):
        self._log = log

    def on_message(self, message):
        state, response = self._state.on_message(message)
        self._state = state

    def on_message_from_bottom(self, eventobj: Event):
        print(f"{EventTypes.MFRT} {self.componentname}.{self.componentinstancenumber}")
        self.on_message(eventobj)

    def send_message(self, message):
        self.send_down(Event(self, EventTypes.MFRT, message))

    # also means start election
    def on_init(self, eventobj: Event):
        self._state.set_server(self)
