from Routing.SSBR.HelperFunctions import SSBRRouteSearchMessage, SSBRUnicastMessage, messageParser
from Ahc import ComponentModel, Event, EventTypes

class ApplicationAndNetwork(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationAndNetwork, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.RoutingTable = {}
        self.Response_Record = {}

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        #evt = Event(self, EventTypes.MFRT, messageGenerator(self))
        #self.send_down(evt)

    def on_message_from_bottom(self, eventobj: Event):
        messagePayload = eventobj.eventcontent.payload
        messageFrom = eventobj.eventcontent.header.messagefrom
        print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")
        if eventobj.eventcontent.header.messagetype == "ROUTECOMPLETED":
            target = int(eventobj.eventcontent.header.messageto.split("-")[1])
            evt = Event(self, EventTypes.MFRT, SSBRUnicastMessage(self, target, "test"))
            self.send_down(evt)
        if eventobj.eventcontent.header.messageto != str(self.componentname) + "-" + str(self.componentid):
            evt = Event(self, EventTypes.MFRT, messageParser(self, eventobj))
            self.send_down(evt)


    def send_test_message(self):
        evt = Event(self, EventTypes.MFRT, SSBRRouteSearchMessage(self))
        self.send_down(evt) 

    def send_SSBR_unicast_message(self, target):
        evt = Event(self, EventTypes.MFRT, SSBRUnicastMessage(self, target))
        self.send_down(evt) 



