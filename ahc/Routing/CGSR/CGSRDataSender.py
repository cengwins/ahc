from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class DataSender(ComponentModel):
    def __init__(self, componentname, componentid):
        super(DataSender, self).__init__(componentname, componentid)
        pass

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == "CGSRRouter":
            self.send_up(eventobj)


    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)
