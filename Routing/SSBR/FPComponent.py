from Routing.SSBR.HelperFunctions import messageParser, SSBRRouteSearchMessage
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
            print("lalala")
        else: 
            evt = Event(self, EventTypes.MFRT, messageParser(self,eventobj))
            self.send_down(evt)
    
    def build_routing_table(self, target):
        SelfDRP = ComponentRegistry().get_component_by_key("DRP",self.componentid)
        SelfDRP.routingTableFlag = True
        evt = Event(self, EventTypes.MFRT, SSBRRouteSearchMessage(self, target))
        self.send_down(evt) 

    def on_message_from_peer(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == "ROUTEREPLY":
            print(f"routereply is here - #{self.componentid}")
            print(eventobj.eventcontent)
            print("\n")
            evt = Event(self, EventTypes.MFRT,messageParser(self,eventobj))
            self.send_down(evt)
        if eventobj.eventcontent.header.messagetype == "ROUTESEARCH" or "ROUTEREPLY":
            evt = Event(self, EventTypes.MFRT,messageParser(self,eventobj))
            self.send_down(evt)
        else:
            evt = Event(self, EventTypes.MFRB,messageParser(self,eventobj))
            self.send_up(evt) # send incoming messages to upper components

    #def editRoutingTable(self, item, mode):
        
    def printRoutingTable(self):
        print(self.routingTable)

    def getRoutingTable(self):
        return self.routingTable


