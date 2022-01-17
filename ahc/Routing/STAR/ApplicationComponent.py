import logging
import threading

from ahc.Ahc import *
from ahc.Routing.STAR.STARNodeComponent import STARMessageTypes
from ahc.Routing.STAR.helper import MessageGenerator, STARTestBenchConfig

logger = logging.getLogger(__name__)


class ApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationComponent, self).__init__(componentname, componentid)
        self.generator = MessageGenerator(mps=STARTestBenchConfig.MPS, sender_fn=self.send_app_message)

    def on_init(self, eventobj: Event):
        threading.Timer(STARTestBenchConfig.WARM_UP, self.start_flow).start()

    def send(self, to, msg):
        message_header = GenericMessageHeader(STARMessageTypes.APP, self.componentinstancenumber, to)
        message = GenericMessage(message_header, GenericMessagePayload(msg))
        kickstarter = Event(self, EventTypes.MFRT, message)
        logger.debug(f"AppLayer {self.componentinstancenumber} sends message to AppLayer {to}")

        self.send_down(kickstarter)

    def on_message_from_bottom(self, eventobj: Event):
        message_from = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload.messagepayload

        logger.debug(f"AppLayer {self.componentinstancenumber} got message: {payload} from {message_from}")

    def start_flow(self):
        self.generator.start()

    def terminate(self):
        super().terminate()
        self.generator.terminate()

    def send_app_message(self):
        dest = self.componentinstancenumber
        neighbors = Topology().get_neighbors(self.componentinstancenumber)

        while dest == self.componentinstancenumber or dest in neighbors:
            dest = Topology().get_random_node().componentinstancenumber

        shortest_hop_count = len(Topology().allpairs_shortest_path()[self.componentinstancenumber][dest]) - 2
        hop_count = 0

        self.send(dest, {
            'text': 'Hello, World!',
            'from': self.componentinstancenumber,
            'to': dest,
            'shortest': shortest_hop_count,
            'hop_count': hop_count
        })
