from Ahc import ComponentModel, Event, ConnectorTypes
from Routing.SSBR.ApplicationAndNetworkComponent import ApplicationAndNetwork
from Routing.SSBR.FPComponent import FP
from Routing.SSBR.NetworkInterfaceComponent import NetworkInterface
from Routing.SSBR.DRPComponent import DRP

# Encapsulator for the SSBR Node
class SSBRNode(ComponentModel):
    def __init__(self, componentname, componentid):
        super(SSBRNode, self).__init__(componentname, componentid)
        self.componentid = componentid
        self.ApplicationAndNetwork = ApplicationAndNetwork(ApplicationAndNetwork.__name__, componentid)
        self.FP = FP(FP.__name__, componentid)
        self.DRP = DRP(DRP.__name__, componentid)
        self.NetworkInterface = NetworkInterface(NetworkInterface.__name__, componentid)
        
        #   Building SSBR Connections
        self.ApplicationAndNetwork.connect_me_to_component(ConnectorTypes.DOWN, self.FP)
        
        self.FP.connect_me_to_component(ConnectorTypes.UP, self.ApplicationAndNetwork)
        self.FP.connect_me_to_component(ConnectorTypes.DOWN, self.NetworkInterface)

        self.DRP.connect_me_to_component(ConnectorTypes.PEER, self.FP)

        self.NetworkInterface.connect_me_to_component(ConnectorTypes.UP, self.DRP)

    def on_init(self, eventobj: Event):
        print(f"{self.componentname} - #{self.componentid} is up.\n")
        pass

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj) # send incoming messages to upper components

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj) # send incoming messages from upper components to a channel

