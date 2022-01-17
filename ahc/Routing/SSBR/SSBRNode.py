from ahc.Ahc import ComponentModel, Event, ConnectorTypes, EventTypes, Topology
from ahc.Routing.SSBR.ApplicationAndNetworkComponent import ApplicationAndNetwork
from ahc.Routing.SSBR.FPComponent import FP
from ahc.Routing.SSBR.NetworkInterfaceComponent import NetworkInterface
from ahc.Routing.SSBR.DRPComponent import DRP
from ahc.Routing.SSBR.HelperFunctions import messageParser, sendMessageToOtherNode

# Encapsulator for the SSBR Node
class SSBRNode(ComponentModel):
    def __init__(self, componentname, componentid):
        super(SSBRNode, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.ApplicationAndNetwork = ApplicationAndNetwork(ApplicationAndNetwork.__name__, componentid)
        self.FP = FP(FP.__name__, componentid)
        self.DRP = DRP(DRP.__name__, componentid)
        self.NetworkInterface = NetworkInterface(NetworkInterface.__name__, componentid)
        self.messageFrom = -1
        
        #   Building SSBR Connections
        self.ApplicationAndNetwork.connect_me_to_component(ConnectorTypes.DOWN, self.FP)
        
        self.FP.connect_me_to_component(ConnectorTypes.UP, self.ApplicationAndNetwork)
        self.FP.connect_me_to_component(ConnectorTypes.DOWN, self.NetworkInterface)

        self.DRP.connect_me_to_component(ConnectorTypes.PEER, self.FP)

        self.NetworkInterface.connect_me_to_component(ConnectorTypes.UP, self.DRP)

        self.NetworkInterface.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.NetworkInterface)

    def on_init(self, eventobj: Event):
        self.neighbors = Topology().get_neighbors(self.componentinstancenumber) #get neighbours
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        pass

    def on_message_from_bottom(self, eventobj: Event):
       
        evt = Event(self, EventTypes.MFRB,messageParser(self,eventobj))    
        self.send_up(evt) # send incoming messages to upper components

    def on_message_from_top(self, eventobj: Event):
        if eventobj.eventcontent.header.interfaceid != float("inf") and self.messageFrom == -1:
                messageFrom = int(eventobj.eventcontent.header.interfaceid.split("-")[0])
                if int(eventobj.eventcontent.header.interfaceid.split("-")[0]) == int(self.componentinstancenumber):
                    messageFrom = int(eventobj.eventcontent.header.interfaceid.split("-")[1])
                self.messageFrom = messageFrom
        if eventobj.eventcontent.header.messagetype == "ROUTESEARCH":
            
            for neigh in self.neighbors:
                if(int(self.messageFrom) != int(neigh)):
                    evt = Event(self, EventTypes.MFRT,sendMessageToOtherNode(self, eventobj, neigh))
                    self.send_down(evt)   # send incoming messages from upper components to a channel
        elif eventobj.eventcontent.header.messagetype == "ROUTEREPLY":
            messageTo = self.messageFrom
            evt = Event(self, EventTypes.MFRT,sendMessageToOtherNode(self, eventobj, messageTo))
            self.send_down(evt)
        elif eventobj.eventcontent.header.messagetype == "UNICASTDATA":
            messageTo = eventobj.eventcontent.header.nexthop
            evt = Event(self, EventTypes.MFRT,sendMessageToOtherNode(self, eventobj, messageTo))
            self.send_down(evt)
       

