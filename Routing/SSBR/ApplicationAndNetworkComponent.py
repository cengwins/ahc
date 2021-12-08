from Routing.SSBR.HelperFunctions import messageGenerator, messageParser
from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class ApplicationAndNetwork(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationAndNetwork, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.RoutingTable = {}
        self.Response_Record = {}

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")

        evt = Event(self, EventTypes.MFRT, messageGenerator(self))
        self.send_down(evt)

    def on_message_from_bottom(self, eventobj: Event):
        messagePayload = eventobj.eventcontent.payload
        messageFrom = eventobj.eventcontent.header.messagefrom
        print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")
        #evt = Event(self, EventTypes.MFRB, "B to higher layer")
        #self.send_up(evt)



