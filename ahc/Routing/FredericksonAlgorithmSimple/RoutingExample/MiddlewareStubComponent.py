from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class MiddlewareMessageStub(ComponentModel):
    def __init__(self, componentname, componentid):
        super(MiddlewareMessageStub, self).__init__(componentname, componentid)
        pass

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == "FredericksonAlgorithmSimpleComponent" or message_target == "Coordinator":
            self.send_up(eventobj)


    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)

