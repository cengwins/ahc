from Ahc import ComponentModel, Event
from Constants import GSR_ROUTER_NAME, GSR_COORDINATOR_NAME


class GSRMiddlewareMessageStub(ComponentModel):
    def __init__(self, componentname, componentid):
        super(GSRMiddlewareMessageStub, self).__init__(componentname, componentid)
        pass

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == GSR_ROUTER_NAME or message_target == GSR_COORDINATOR_NAME:
            self.send_up(eventobj)
        else:
            print(f"VVVVVVVVVVVV******** {message_target}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)