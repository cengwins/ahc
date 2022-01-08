from Ahc import ComponentModel, Event, ConnectorTypes
from GSRTestingApplicationComponent import GSRTestingApplicationComponent
from Routing.GSR.GSRCoordinatorComponent import GSRCoordinator
from Routing.GSR.GSRMiddlewareStubComponent import GSRMiddlewareMessageStub
from Routing.GSR.RoutingGSRComponent import RoutingGSRComponent


# Encapsulator for the Application Node
class GSRTestingNode(ComponentModel):
    def __init__(self, componentname, componentid):
        super(GSRTestingNode, self).__init__(componentname, componentid)
        self.Application = GSRTestingApplicationComponent(GSRTestingApplicationComponent.__name__, componentid)
        self.Coordinator = GSRCoordinator(GSRCoordinator.__name__, componentid)
        self.GSRComponent = RoutingGSRComponent(RoutingGSRComponent.__name__, componentid)
        self.MiddlewareStub = GSRMiddlewareMessageStub(GSRMiddlewareMessageStub.__name__, componentid)

        # Application layer only talks with Coordinator,
        # Coordinator coordinates all demands of the application by triggering other components if necessary...
        self.Application.connect_me_to_component(ConnectorTypes.DOWN, self.Coordinator)
        self.Coordinator.connect_me_to_component(ConnectorTypes.UP, self.Application)
        self.Coordinator.connect_me_to_component(ConnectorTypes.PEER, self.GSRComponent)
        self.Coordinator.connect_me_to_component(ConnectorTypes.DOWN, self.MiddlewareStub)


        self.GSRComponent.connect_me_to_component(ConnectorTypes.PEER, self.Coordinator)

        self.GSRComponent.connect_me_to_component(ConnectorTypes.DOWN, self.MiddlewareStub)
        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.UP, self.GSRComponent)
        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.UP, self.Coordinator)
        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.MiddlewareStub)

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj) # send incoming messages to upper components

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj) # send incoming messages from upper components to a channel
