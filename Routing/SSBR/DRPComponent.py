from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class DRP(ComponentModel):
    def __init__(self, componentname, componentid):
        super(DRP, self).__init__(componentname, componentid)
        self.RoutingTable = {}
        self.Response_Record = {}

    def on_init(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        #evt = Event(self, EventTypes.MFRP, "Network interface to peers")
        #self.send_peer(evt)

    def on_message_from_top(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")

    def on_message_from_bottom(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        evt = Event(self, EventTypes.MFRB, "B to higher layer")
        self.send_up(evt)

    def on_message_from_peer(self, eventobj: Event):
        print(f"I am {self.componentname}, got message from peer, eventcontent={eventobj.eventcontent}\n")


