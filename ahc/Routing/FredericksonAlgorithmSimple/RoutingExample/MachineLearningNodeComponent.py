from ahc.Ahc import ComponentModel, Event, ConnectorTypes
from Routing.FredericksonAlgorithmSimple.RoutingExample.ApplicationComponent import ApplicationComponent
from Routing.FredericksonAlgorithmSimple.RoutingExample.CoordinatorComponent import Coordinator
from Routing.FredericksonAlgorithmSimple.RoutingExample.FredericksonAlgorithmSimpleComponent import FredericksonAlgorithmSimpleComponent
from Routing.FredericksonAlgorithmSimple.RoutingExample.MiddlewareStubComponent import MiddlewareMessageStub

# Encapsulator for the Application Node
class MachineLearningNode(ComponentModel):
    def __init__(self, componentname, componentid):
        super(MachineLearningNode, self).__init__(componentname, componentid)
        self.Application = ApplicationComponent(ApplicationComponent.__name__, componentid)
        self.Coordinator = Coordinator(Coordinator.__name__, componentid)
        self.FrederickAlgorithmSimpleComponent = FredericksonAlgorithmSimpleComponent(FredericksonAlgorithmSimpleComponent.__name__, componentid)
        self.MiddlewareStub = MiddlewareMessageStub(MiddlewareMessageStub.__name__, componentid)

        # Application layer only talks with Coordinator,
        # Coordinator coordinates all demands of the application by triggering other components if necessary...
        self.Application.connect_me_to_component(ConnectorTypes.DOWN, self.Coordinator)
        self.Coordinator.connect_me_to_component(ConnectorTypes.UP, self.Application)
        self.Coordinator.connect_me_to_component(ConnectorTypes.PEER, self.FrederickAlgorithmSimpleComponent)
        self.Coordinator.connect_me_to_component(ConnectorTypes.DOWN, self.MiddlewareStub)

        self.FrederickAlgorithmSimpleComponent.connect_me_to_component(ConnectorTypes.PEER, self.Coordinator)

        self.FrederickAlgorithmSimpleComponent.connect_me_to_component(ConnectorTypes.DOWN, self.MiddlewareStub)
        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.UP, self.FrederickAlgorithmSimpleComponent)
        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.UP, self.Coordinator)

        self.MiddlewareStub.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.MiddlewareStub)

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj) # send incoming messages to upper components

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj) # send incoming messages from upper components to a channel

