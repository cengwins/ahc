from timeit import default_timer as timer

from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes
from ahc.Routing.GSR.Constants import GSR_APPLICATION_NAME, GSR_COORDINATOR_NAME, ROUTING_COMPLETED_MESSAGE_TYPE, INFO_MESSAGE_TYPE


class GSRTestingApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(GSRTestingApplicationComponent, self).__init__(componentname, componentid)
        self.start_time = None
        self.end_time = None

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        message_to = event_header.messageto.split("-")[0]
        message_type = event_header.messagetype
        message = eventobj.eventcontent.payload
        if message_to == GSR_APPLICATION_NAME:
            if message_type == INFO_MESSAGE_TYPE:
                source = message["src"]
                content = message["content"]
                print(f"App {self.componentinstancenumber} has received {content} from {source}")
                self.send_info_message(source, "PING")
            elif message_type == ROUTING_COMPLETED_MESSAGE_TYPE:
                self.end_time = timer()
                print(f"App {self.componentinstancenumber} has received RoutingCompleted message")
                for i in range(1, 5):
                    payload = "PONG " + str(i)
                    self.send_info_message(i, payload)

    def send_info_message(self, dest, payload):
        message_header = GenericMessageHeader(
            INFO_MESSAGE_TYPE,
            GSR_APPLICATION_NAME + "-" + str(self.componentinstancenumber),
            GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber))
        payload = {
            "src": self.componentinstancenumber,
            "dest": dest,
            "content": payload
        }
        message = GenericMessage(message_header, payload)
        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event)

    def get_duration(self):
        return self.end_time - self.start_time
