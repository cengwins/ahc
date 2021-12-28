from Routing.SSBR.HelperFunctions import messageParser, SSBRRouteSearchMessage, SSBRUnicastMessageFPParser
from Ahc import ComponentModel, Event, EventTypes, ComponentRegistry

class FP(ComponentModel):
    def __init__(self, componentname, componentid):
        super(FP, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.routingTable = {}
        
    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        #evt = Event(self, EventTypes.MFRP, "Network interface to peers")
        #self.send_peer(evt)

    def on_message_from_top(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagetype == "UNICASTDATA"):
            evt = Event(self, EventTypes.MFRT, SSBRUnicastMessageFPParser(self, eventobj))
            self.send_down(evt)
        else: 
            evt = Event(self, EventTypes.MFRT, messageParser(self, eventobj))
            self.send_down(evt)
    
    def build_routing_table(self, target):
        SelfDRP = ComponentRegistry().get_component_by_key("DRP", self.componentid)
        SelfDRP.routingTableFlag = True
        evt = Event(self, EventTypes.MFRT, SSBRRouteSearchMessage(self, target))
        self.send_down(evt)
        
    def on_message_from_peer(self, eventobj: Event):
        
        if eventobj.eventcontent.header.messagetype == "ROUTESEARCH":
            evt = Event(self, EventTypes.MFRT,messageParser(self,eventobj))
            self.send_down(evt)

        elif eventobj.eventcontent.header.messagetype == "ROUTEREPLY":
            payload = eventobj.eventcontent.payload
            
            for el in payload:
                    self.routingTable[str(el)] = payload[len(payload)-1]

            if int(eventobj.eventcontent.header.messageto.split("-")[1]) == self.componentid:
                print("Routing table is completed....\n")

            else:
                evt = Event(self, EventTypes.MFRT,messageParser(self,eventobj))
                self.send_down(evt)
            
        else:
            evt = Event(self, EventTypes.MFRB,messageParser(self,eventobj))
            self.send_up(evt) # send incoming messages to upper components
        
    def printRoutingTable(self):
        print(self.routingTable)

    def getRoutingTable(self):
        return self.routingTable


