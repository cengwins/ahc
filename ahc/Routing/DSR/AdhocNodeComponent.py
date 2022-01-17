from copy import deepcopy
from ahc.Ahc import ComponentModel
from ahc.Ahc import ConnectorTypes
from ahc.Ahc import Event
from ahc.Ahc import EventTypes
from ahc.Ahc import GenericMessage
from ahc.Ahc import GenericMessageHeader
from ahc.Routing.DSR.ApplicationComponent import ApplicationComponent
from ahc.Routing.DSR.DSRAlgorithmComponent import DSRAlgorithmComponent
from ahc.Routing.DSR.DSRAlgorithmComponent import MessageTypes


class AdhocNodeComponent(ComponentModel):
    def __init__(self, component_name, component_id):
        super(AdhocNodeComponent, self).__init__(component_name, component_id)
        self.Application = ApplicationComponent(ApplicationComponent.__name__, component_id)
        self.DSRAlgorithmComponent = DSRAlgorithmComponent(DSRAlgorithmComponent.__name__, component_id)

        self.Application.connect_me_to_component(ConnectorTypes.DOWN, self.DSRAlgorithmComponent)
        self.DSRAlgorithmComponent.connect_me_to_component(ConnectorTypes.UP, self.Application)

        self.DSRAlgorithmComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.DSRAlgorithmComponent)

    def send_unicast_message(self, next_hop, payload):
        src = str(self.componentinstancenumber)
        dst = str(next_hop)
        header = GenericMessageHeader("MessageTypeHere",
                                      self.componentname + "-" + src,
                                      self.componentname + "-" + dst,
                                      interfaceid=src + "-" + dst)

        message = GenericMessage(header, payload)

        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event)

    def send_broadcast_message(self, payload):
        for interface in self.connectors[ConnectorTypes.DOWN]:
            for next_hop in interface.componentinstancenumber.split("-"):
                if int(next_hop) != self.get_component_id():
                    self.send_unicast_message(next_hop, payload)

    def send_message(self, next_hop, payload):
        if str("inf") == next_hop:
            self.send_broadcast_message(payload)
        else:
            self.send_unicast_message(next_hop, payload)

    def get_next_component_id(self, route: list):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_next_component = index_of_current_component + 1
            return route[index_of_next_component]
        except ValueError:
            print("[AdhocNodeComponent:get_next_component_id][Exception] ValueError")
            print("[AdhocNodeComponent:get_next_component_id][Exception] comp_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("[AdhocNodeComponent:get_next_component_id][Exception] route = " + str_route)
            return None

    def get_prev_component_id(self, route: list):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_prev_component = index_of_current_component - 1
            return route[index_of_prev_component]
        except ValueError:
            print("[AdhocNodeComponent:get_prev_component_id][Exception] ValueError")
            print("[AdhocNodeComponent:get_prev_component_id][Exception] comp_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("[AdhocNodeComponent:get_prev_component_id][Exception] route = " + str_route)
            return None

    def get_component_id(self) -> int:
        return self.componentinstancenumber

    def on_message_from_bottom(self, eventobj: Event):

        message_type = eventobj.eventcontent.payload.header.messagetype
        message_from = eventobj.eventcontent.payload.header.messagefrom
        message_to = eventobj.eventcontent.payload.header.messageto

        message_header = GenericMessageHeader(message_type,
                                              message_from,
                                              message_to)

        message_payload = eventobj.eventcontent.payload.payload
        message = GenericMessage(message_header, message_payload)

        event = Event(self, EventTypes.MFRB, message)
        self.send_up(event)

    def is_link_up(self, next_hop) -> bool:

        for interface in self.connectors[ConnectorTypes.DOWN]:
            if interface.componentinstancenumber.split("-")[0] == str(self.componentinstancenumber):
                interface_next_hop = interface.componentinstancenumber.split("-")[1]
                if interface_next_hop == str(next_hop):
                    return True
            else:
                interface_next_hop = interface.componentinstancenumber.split("-")[0]
                if interface_next_hop == str(next_hop):
                    return True

        return False

    def on_message_from_top(self, eventobj: Event):

        src = int(eventobj.eventcontent.header.messagefrom.split("-")[1])

        message_type = eventobj.eventcontent.header.messagetype
        route = deepcopy(eventobj.eventcontent.payload[0])

        next_hop = None
        if MessageTypes.ROUTE_REQUEST == message_type:
            next_hop = str("inf")
        elif MessageTypes.ROUTE_REPLY == message_type:
            next_hop = self.get_prev_component_id(route)
        elif MessageTypes.ROUTE_ERROR == message_type:
            next_hop = self.get_prev_component_id(route)
        elif MessageTypes.ROUTE_FORWARDING == message_type:
            next_hop = self.get_next_component_id(route)

        if next_hop is not None:
            self.send_message(next_hop, eventobj.eventcontent)

        if MessageTypes.ROUTE_FORWARDING == message_type:
            if not self.is_link_up(next_hop):
                self.start_route_error_message(src, next_hop, route)

    def start_route_error_message(self, src, next_hop, route):

        try:
            new_src = self.get_component_id()
            new_dst = src

            header = GenericMessageHeader(MessageTypes.ROUTE_ERROR,
                                          self.componentname + "-" + str(new_src),
                                          self.componentname + "-" + str(new_dst))

            index_of_current_component = route.index(self.get_component_id())
            new_route = route[0: index_of_current_component]

            broken_link = [self.get_component_id(), next_hop]

            event = Event(self,
                          EventTypes.MFRB,
                          GenericMessage(header,
                                         [new_route, broken_link]))

            self.send_up(event)

        except ValueError:
            print("[AdhocNodeComponent:send_route_error][Error] component_id not in the route")
            print("[AdhocNodeComponent:send_route_error][Error] comp_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("[AdhocNodeComponent:send_route_error][Error] route = " + str_route)
