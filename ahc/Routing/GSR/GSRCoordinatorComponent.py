from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes
from ahc.Routing.GSR.Constants import TERMINATE_MESSAGE_TYPE, \
    INFO_MESSAGE_TYPE, \
    ROUTING_COMPLETED_MESSAGE_TYPE, \
    GSR_COORDINATOR_NAME, \
    GSR_ROUTER_NAME, \
    GSR_APPLICATION_NAME, \
    ENABLE_NETWORK_LEVEL_LOGGING


class GSRCoordinator(ComponentModel):
    def __init__(self, component_name, component_id):
        super(GSRCoordinator, self).__init__(component_name, component_id)
        self.routing_table = {}

    def on_message_from_top(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        sender = event_header.messagefrom.split("-")[0]
        message_to = event_header.messageto.split("-")[0]
        message_type = event_header.messagetype
        message = eventobj.eventcontent.payload
        if ENABLE_NETWORK_LEVEL_LOGGING:
            print(f"Coordinator {self.componentinstancenumber} receives message from top")
        if message_to == GSR_COORDINATOR_NAME:
            if sender == GSR_APPLICATION_NAME and message_type == TERMINATE_MESSAGE_TYPE:
                self.terminate_routing()
            elif sender == GSR_APPLICATION_NAME and message_type == INFO_MESSAGE_TYPE:
                self.route_message(message)

    def on_message_from_peer(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        sender = event_header.messagefrom.split("-")[0]
        message_to = event_header.messageto.split("-")[0]
        message = eventobj.eventcontent.payload
        if message_to == GSR_COORDINATOR_NAME:
            if sender == GSR_ROUTER_NAME:
                self.routing_table = message["routing_table"]
                if ENABLE_NETWORK_LEVEL_LOGGING:
                    print(f"Coordinator {self.componentinstancenumber} has received Routing Table")
                if self.componentinstancenumber == 0:
                    message_header = GenericMessageHeader(
                        ROUTING_COMPLETED_MESSAGE_TYPE,
                        GSR_COORDINATOR_NAME + "-0",
                        GSR_APPLICATION_NAME + "-0")
                    message = GenericMessage(message_header, {"n_nodes": len(self.routing_table)})
                    kickstarter = Event(self, EventTypes.MFRB, message)
                    self.send_up(kickstarter)

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        sender = event_header.messagefrom.split("-")[0]
        message_to = event_header.messageto.split("-")[0]
        message_type = event_header.messagetype
        message = eventobj.eventcontent.payload
        if message_to == GSR_COORDINATOR_NAME:
            if sender == GSR_COORDINATOR_NAME and message_type == INFO_MESSAGE_TYPE:
                dest = message["dest"]
                src = message["src"]
                if ENABLE_NETWORK_LEVEL_LOGGING:
                    print(f"Coordinator {self.componentinstancenumber} has received info message from {src} to {dest}")

                if dest == self.componentinstancenumber:
                    message_header = GenericMessageHeader(
                        message_type,
                        GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber),
                        GSR_APPLICATION_NAME + "-" + str(self.componentinstancenumber))
                    message_to_application = GenericMessage(message_header, message)
                    event = Event(self, EventTypes.MFRB, message_to_application)
                    self.send_up(event)
                    # send to app layer
                    pass
                else:
                    self.route_message(message)

    def terminate_routing(self):
        message_from = GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber)
        message_to = GSR_ROUTER_NAME + "-" + str(self.componentinstancenumber)
        message_header = GenericMessageHeader(TERMINATE_MESSAGE_TYPE,
                                              message_from,
                                              message_to)
        message = GenericMessage(message_header, "")
        event = Event(self, EventTypes.MFRP, message)
        self.send_peer(event)
        if ENABLE_NETWORK_LEVEL_LOGGING:
            print("SENDING [" + message_from + " -> " + message_to + "]: TERMINATE")

    def route_message(self, message_to_route):
        if len(self.routing_table) > 0:
            message_from = GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber)
            dest = message_to_route["dest"]
            neighbor_id = self.routing_table[dest]
            message_to = GSR_COORDINATOR_NAME + "-" + str(neighbor_id)
            interface_id = str(self.componentinstancenumber) + "-" + str(neighbor_id)
            message_header = GenericMessageHeader(
                INFO_MESSAGE_TYPE,
                message_from,
                message_to,
                interfaceid=interface_id
            )
            message = GenericMessage(message_header, message_to_route)

            event = Event(self, EventTypes.MFRT, message)
            self.send_down(event)
            if ENABLE_NETWORK_LEVEL_LOGGING:
                print("ROUTING [" + message_from + " -> " + message_to + "]: " + str(message.payload))
