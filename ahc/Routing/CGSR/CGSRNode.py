from ahc.Ahc import ComponentModel, Event, GenericMessage, ConnectorTypes, GenericMessageHeader, EventTypes, \
    ComponentRegistry, Lock, Thread, Topology
from ahc.Routing.CGSR.CGSR import CGSRRouter
from ahc.Routing.CGSR.CGSRControlComponent import CGSRControlComponent
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.CGSR.CGSRDataSender import DataSender

class CGSRNode(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    def __init__(self, componentname, componentid):
        super(CGSRNode, self).__init__(componentname, componentid)
        self.CGSRControlComponent = CGSRControlComponent(CGSRNode.__name__, componentid)
        self.CGSRRouter = CGSRRouter(CGSRNode.__name__, componentid)
        self.DataSender = DataSender(DataSender.__name__, componentid)

        self.CGSRControlComponent.connect_me_to_component(ConnectorTypes.PEER, self.CGSRRouter)
        self.CGSRRouter.connect_me_to_component(ConnectorTypes.PEER, self.CGSRControlComponent)

        self.CGSRRouter.connect_me_to_component(ConnectorTypes.DOWN, self.DataSender)
        self.DataSender.connect_me_to_component(ConnectorTypes.UP, self.CGSRRouter)

        self.DataSender.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.DataSender)

        # super(CGSRNode, self).__init__(componentname, componentid)
        super().__init__(componentname, componentid)

