from ahc.Routing.SSBR.HelperFunctions import SSBRRouteSearchMessage, SSBRUnicastMessage, messageParser
from ahc.Ahc import ComponentModel, Event, EventTypes

class ApplicationAndNetwork(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationAndNetwork, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.Response_Record = {}

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        #evt = Event(self, EventTypes.MFRT, messageGenerator(self))
        #self.send_down(evt)

    def on_message_from_bottom(self, eventobj: Event):
        messagePayload = eventobj.eventcontent.payload
        messageFrom = eventobj.eventcontent.header.messagefrom
        #print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")

        if eventobj.eventcontent.header.messagetype == "UNICASTDATA":
            if eventobj.eventcontent.payload == "benchmark test message":
                evt = Event(self, EventTypes.MFRT, SSBRUnicastMessage(self, eventobj.eventcontent.header.messageto, eventobj.eventcontent.payload))
                self.send_down(evt) 
            else:
                print(f"Message from {eventobj.eventcontent.header.messagefrom} is delivered to {self.componentname}-{self.componentid}. Message is - {eventobj.eventcontent.payload}")
                if eventobj.eventcontent.header.messageto != str(self.componentname) + "-" + str(self.componentid):
                    evt = Event(self, EventTypes.MFRT, messageParser(self, eventobj))
                    self.send_down(evt)


    def send_test_message(self):
        evt = Event(self, EventTypes.MFRT, SSBRRouteSearchMessage(self))
        self.send_down(evt) 

    def send_SSBR_unicast_message(self, target, message=""):
        evt = Event(self, EventTypes.MFRT, SSBRUnicastMessage(self, target, message))
        self.send_down(evt) 



