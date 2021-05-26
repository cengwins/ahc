from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes
from Routing.TouegAlgorithm.Experiments.ExperimentDataCollector import ExperimentCollector

class MiddlewareMessageStub(ComponentModel):
    def __init__(self, componentname, componentid):
        super(MiddlewareMessageStub, self).__init__(componentname, componentid)
        pass

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == "TouegRoutingComponent" or message_target == "Coordinator":
            self.send_up(eventobj)
        else:
            print(f"VVVVVVVVVVVV******** {message_target}")


    def on_message_from_top(self, eventobj: Event):
        if self.componentinstancenumber not in ExperimentCollector().MESSAGE_COUNT:
            ExperimentCollector().MESSAGE_COUNT[self.componentinstancenumber] = 1
        else:
            ExperimentCollector().MESSAGE_COUNT[self.componentinstancenumber] += 1

        self.send_down(eventobj)

