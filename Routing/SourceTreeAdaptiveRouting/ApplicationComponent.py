import logging

from Ahc import *
from Routing.SourceTreeAdaptiveRouting.STARNodeComponent import STARMessageTypes
from Routing.SourceTreeAdaptiveRouting.helper import STARStats, STARStatEvent

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s [%(levelname)s] - %(message)s')
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class ApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationComponent, self).__init__(componentname, componentid)

    def send_message(self, to, msg):
        message_header = GenericMessageHeader(STARMessageTypes.APP, self.componentinstancenumber, to)
        message = GenericMessage(message_header, GenericMessagePayload(msg))
        kickstarter = Event(self, EventTypes.MFRT, message)
        logger.info(f"AppLayer {self.componentinstancenumber} sends message to AppLayer {to}")
        STARStats().emit(STARStatEvent.APP_MSG_SENT)

        self.send_down(kickstarter)

    def on_message_from_bottom(self, eventobj: Event):
        message_from = eventobj.eventcontent.header.messagefrom
        payload = eventobj.eventcontent.payload.messagepayload

        logger.info(f"AppLayer {self.componentinstancenumber} got message: {payload} from {message_from}")
        STARStats().emit(STARStatEvent.APP_MSG_RECV)
