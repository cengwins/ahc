from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology

class RoutingAODVComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber):
        super(RoutingAODVComponent, self).__init__(componentname, componentinstancenumber)
