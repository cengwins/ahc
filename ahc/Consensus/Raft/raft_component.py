import sys

from ahc.Ahc import ComponentModel, EventTypes, ConnectorTypes
from ahc.Ahc import Event

from ahc.Consensus.Raft.states import Follower
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
