from Routing.SSBR.HelperFunctions import messageParser
from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class DRP(ComponentModel):
    def __init__(self, componentname, componentid):
        super(DRP, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.RoutingTable = {}
        self.Response_Record = {}

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        #evt = Event(self, EventTypes.MFRP, "Network interface to peers")
        #self.send_peer(evt)

    def on_message_from_bottom(self, eventobj: Event):      
        evt = Event(self, EventTypes.MFRP,messageParser(self, eventobj))
        self.send_peer(evt)
       


