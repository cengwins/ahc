from Routing.SSBR.HelperFunctions import messageParser
from Ahc import ComponentModel, Event, EventTypes
from Routing.SSBR.HelperFunctions import SSBRRouteReplyMessage

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
        if(eventobj.eventcontent.header.messagetype == "ROUTESEARCH"):
            messagefrom = eventobj.eventcontent.header.messagefrom
            messageto = eventobj.eventcontent.header.messageto
            if self.routingTableFlag == False:
                messageFromID = int(messagefrom.split("-")[1])
                tableVal = self.signalStabilityTable.get(messageFromID)
                if tableVal == "SC":
                    self.routingTableFlag = True
                    evt = Event(self, EventTypes.MFRP,messageParser(self, eventobj))
                    self.send_peer(evt)
                if int(messageto.split("-")[1]) == int(self.componentid):
                    evt = Event(self, EventTypes.MFRP, SSBRRouteReplyMessage(self, eventobj))
                    self.send_peer(evt)
            if int(messageto.split("-")[1]) == int(self.componentid):
                evt = Event(self, EventTypes.MFRP, messageParser(self, eventobj))
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
