from ahc.Ahc import ComponentModel, Event, GenericMessage, ConnectorTypes, GenericMessageHeader, EventTypes, \
    ComponentRegistry, Lock, Thread, Topology
from ahc.Routing.OLSR.OLSRSimplifiedComponent import OLSRSimplifiedRouter
from ahc.Routing.OLSR.OLSRPacketSender import OLSRPacketSender
from ahc.Routing.OLSR.OLSRMessageGenerator import OLSRControlComponent

class OLSRNode(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    def __init__(self, componentname, componentid):
        super(OLSRNode, self).__init__(componentname, componentid)
        self.OLSRControlComponent = OLSRControlComponent(OLSRControlComponent.__name__, componentid)
        self.OLSRSimplifiedRouter = OLSRSimplifiedRouter(OLSRSimplifiedRouter.__name__, componentid)
        self.OLSRPacketSender = OLSRPacketSender(OLSRPacketSender.__name__, componentid)


        self.OLSRControlComponent.connect_me_to_component(ConnectorTypes.PEER, self.OLSRSimplifiedRouter)
        self.OLSRSimplifiedRouter.connect_me_to_component(ConnectorTypes.PEER, self.OLSRControlComponent)

        self.OLSRSimplifiedRouter.connect_me_to_component(ConnectorTypes.DOWN, self.OLSRPacketSender)
        self.OLSRPacketSender.connect_me_to_component(ConnectorTypes.UP, self.OLSRSimplifiedRouter)

        self.OLSRPacketSender.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.OLSRPacketSender)

        super().__init__(componentname, componentid)

