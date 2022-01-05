from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes
from RoutingGSRComponent import RoutingGSRComponent


class Coordinator(ComponentModel):
    terminate_message_type = "GSRTERMINATE"
    info_message_type = "INFOMESSAGE"

    def __init__(self, component_name, component_id):
        super(Coordinator, self).__init__(component_name, component_id)
        self.routing_table = {}

    def on_message_from_top(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        sender = event_header.messagefrom.split("-")[0]
        message_to = event_header.messageto.split("-")[0]
        message_type = event_header.messagetype
        message = eventobj.eventcontent.payload
        print(f"Coordinator {self.componentinstancenumber} receives message from top")
        if message_to == Coordinator.__name__:
            if sender == "ApplicationComponent" and message_type == self.terminate_message_type:
                self.terminate_routing()
            elif sender == "ApplicationComponent" and message_type == self.info_message_type:
                self.route_message(message)

    def on_message_from_peer(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        sender = event_header.messagefrom.split("-")[0]
        message_to = event_header.messageto.split("-")[0]
        message = eventobj.eventcontent.payload
        if message_to == Coordinator.__name__:
            if sender == RoutingGSRComponent.__name__:
                self.routing_table = message["routing_table"]
                print(f"Coordinator {self.componentinstancenumber} has received Routing Table")
                if self.componentinstancenumber == 0:
                    message_header = GenericMessageHeader(RoutingGSRComponent.routing_completed_message_type,
                                                          "Coordinator-0",
                                                          "ApplicationComponent-0")
                    message = GenericMessage(message_header, "")
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
        if message_to == Coordinator.__name__:
            if sender == "Coordinator" and message_type == self.info_message_type:
                dest = message["dest"]
                src = message["src"]
                print(f"Coordinator {self.componentinstancenumber} has received info message from {src} to {dest}")

                if dest == self.componentinstancenumber:
                    message_header = GenericMessageHeader(message_type,
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "ApplicationComponent-" + str(self.componentinstancenumber))
                    message_to_application = GenericMessage(message_header, message)
                    event = Event(self, EventTypes.MFRB, message_to_application)
                    self.send_up(event)
                    # send to app layer
                    pass
                else:
                    self.route_message(message)

    def terminate_routing(self):
        message_from = Coordinator.__name__ + "-" + self.componentinstancenumber
        message_to = RoutingGSRComponent.__name__ + "-" + str(self.componentinstancenumber)
        message_header = GenericMessageHeader(RoutingGSRComponent.terminate_routing_message_type,
                                              message_from,
                                              message_to)
        message = GenericMessage(message_header, "")
        event = Event(self, EventTypes.MFRP, message)
        self.send_peer(event)
        print("SENDING [" + message_from + " -> " + message_to + "]: TERMINATE")

    def route_message(self, message_to_route):
        if len(self.routing_table) > 0:
            message_from = Coordinator.__name__ + "-" + str(self.componentinstancenumber)
            dest = message_to_route["dest"]
            neighbor_id = self.routing_table[dest]
            message_to = Coordinator.__name__ + "-" + str(neighbor_id)
            interface_id = str(self.componentinstancenumber) + "-" + str(neighbor_id)
            message_header = GenericMessageHeader(
                self.info_message_type,
                message_from,
                message_to,
                interfaceid=interface_id
            )
            message = GenericMessage(message_header, message_to_route)

            event = Event(self, EventTypes.MFRT, message)
            self.send_down(event)
            print("ROUTING [" + message_from + " -> " + message_to + "]: " + str(message))
