from ahc.Routing.SSBR.HelperFunctions import messageParser
from ahc.Ahc import ComponentModel, Event, EventTypes, ComponentRegistry
from ahc.Routing.SSBR.HelperFunctions import SSBRRouteReplyMessage, SSBRRouteCompletedMessage

class DRP(ComponentModel):
    def __init__(self, componentname, componentid):
        super(DRP, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.signalStabilityTable = {}
        self.routingTableFlag = False

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        #evt = Event(self, EventTypes.MFRP, "Network interface to peers")
        #self.send_peer(evt)

    def on_message_from_bottom(self, eventobj: Event):
        messageto = eventobj.eventcontent.header.messageto
        interfaceID = eventobj.eventcontent.header.interfaceid
        messageFromID = int(interfaceID.split("-")[1])
        #selfFP = ComponentRegistry().get_component_by_key("FP",self.componentid)
        #selfFP.routingTable.get()[int(messageto.split("-")[1])] != None
        if messageFromID == int(self.componentid):
            messageFromID = int(interfaceID.split("-")[0])

        if(eventobj.eventcontent.header.messagetype == "ROUTESEARCH"):
            if self.routingTableFlag == False:
                tableVal = self.signalStabilityTable.get(messageFromID)
                if tableVal == "SC":
                    self.routingTableFlag = True
                    if int(messageto.split("-")[1]) == int(self.componentid):
                        evt = Event(self, EventTypes.MFRP, SSBRRouteReplyMessage(self, eventobj))
                        self.send_peer(evt)
                    else:
                        evt = Event(self, EventTypes.MFRP,messageParser(self, eventobj))
                        self.send_peer(evt)
            

        elif(eventobj.eventcontent.header.messagetype == "ROUTEREPLY"):
                evt = Event(self, EventTypes.MFRP,messageParser(self, eventobj))
                self.send_peer(evt)
            
        else:
            evt = Event(self, EventTypes.MFRP,messageParser(self, eventobj))
            self.send_peer(evt)
    
    def editSignalStabilityTable(self, item, mode):
        if mode == "SC":
            self.signalStabilityTable[item] = "SC"
        else:
            self.signalStabilityTable[item] = "WC"
        
    def printSignalStabilityTable(self):
        print(self.signalStabilityTable)

    def getSignalStabilityTable(self):
        return self.signalStabilityTable
