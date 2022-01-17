from ahc.Routing.SSBR.HelperFunctions import messageParser, SSBRRouteSearchMessage, SSBRUnicastMessageFPParser, SSBRUnicastMessage
from ahc.Ahc import ComponentModel, Event, EventTypes, ComponentRegistry

class FP(ComponentModel):
    def __init__(self, componentname, componentid):
        super(FP, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.routingTable = {}
        self.mode = 0
        self.nodeCount = 0
        
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
    
    def build_routing_table(self, target, mode = 0, node = 0):
        SelfDRP = ComponentRegistry().get_component_by_key("DRP", self.componentid)
        SelfDRP.routingTableFlag = True
        if mode == 1:
            self.mode = 1
            self.nodeCount = node
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
                if self.mode == 1:
                    evt = Event(self, EventTypes.MFRB,SSBRUnicastMessage(self, self.nodeCount-1 , "benchmark test message"))
                    self.send_up(evt)

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


