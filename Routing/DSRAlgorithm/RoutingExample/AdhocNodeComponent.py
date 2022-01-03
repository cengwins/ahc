from Routing.DSRAlgorithm.RoutingExample.ApplicationComponent import ApplicationComponent
from Routing.DSRAlgorithm.DSRAlgorithmComponent import DSRAlgorithmComponent
from Routing.DSRAlgorithm.DSRAlgorithmComponent import MessageTypes
from Ahc import ComponentModel
from Ahc import ConnectorTypes
from Ahc import Event
from Ahc import EventTypes
from Ahc import GenericMessage
from Ahc import GenericMessageHeader

import logging

logging.basicConfig(filename="C:\\Users\\bsezgin\\Desktop\\newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


class AdhocNodeComponent(ComponentModel):
    def __init__(self, component_name, component_id):
        super(AdhocNodeComponent, self).__init__(component_name, component_id)
        self.Application = ApplicationComponent(ApplicationComponent.__name__, component_id)
        self.DSRAlgorithmComponent = DSRAlgorithmComponent(DSRAlgorithmComponent.__name__, component_id)

        self.Application.connect_me_to_component(ConnectorTypes.DOWN, self.DSRAlgorithmComponent)
        self.DSRAlgorithmComponent.connect_me_to_component(ConnectorTypes.UP, self.Application)

        self.DSRAlgorithmComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.DSRAlgorithmComponent)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    def send_unicast_message(self, next_hop, payload):
        src = str(self.componentinstancenumber)
        dst = str(next_hop)
        header = GenericMessageHeader("MessageTypeHere",
                                      self.componentname + "-" + src,
                                      self.componentname + "-" + dst,
                                      interfaceid=src + "-" + dst)

        message = GenericMessage(header, payload)
        event = Event(self, EventTypes.MFRT, message)

        self.logger.debug("[AdhocNode::unicast] src = " + src + " => dst = " + dst)

        self.send_down(event)

    def send_broadcast_message(self, payload):
        for connector_type in self.connectors:
            if ConnectorTypes.DOWN == connector_type:
                for interface in self.connectors[connector_type]:
                    next_hop = interface.componentinstancenumber.split("-")[1]
                    if int(next_hop) != self.get_component_id():
                        self.send_unicast_message(next_hop, payload)

    def get_next_component_id(self, route: list):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_next_component = index_of_current_component + 1
            return route[index_of_next_component]
        except ValueError:
            print("[MachineLearningNodeComponent:get_next_component_id][Exception] ValueError")
            print("component_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("route = " + str_route)
            return None

    def get_prev_component_id(self, route: list):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_prev_component = index_of_current_component - 1
            return route[index_of_prev_component]
        except ValueError:
            print("[MachineLearningNodeComponent:get_prev_component_id][Exception] ValueError")
            print("component_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("route = " + str_route)
            return None

    def get_component_id(self) -> int:
        return self.componentinstancenumber

    def on_message_from_bottom(self, eventobj: Event):
        self.logger.debug("[AdhocNode::bottom] id = " + str(self.get_component_id()))

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

    def on_message_from_top(self, eventobj: Event):

        src = int(eventobj.eventcontent.header.messagefrom.split("-")[1])

        message_type = eventobj.eventcontent.header.messagetype

        if MessageTypes.ROUTE_REQUEST == message_type:
            self.send_broadcast_message(eventobj.eventcontent)

        elif MessageTypes.ROUTE_REPLY == message_type:
            route = eventobj.eventcontent.payload[0]
            prev_component_id = self.get_prev_component_id(route)

            if prev_component_id is not None:
                self.send_unicast_message(prev_component_id, eventobj.eventcontent)

        elif MessageTypes.ROUTE_ERROR == message_type:
            route = eventobj.eventcontent.payload[0]
            prev_component_id = self.get_prev_component_id(route)

            if prev_component_id is not None:
                self.send_unicast_message(prev_component_id, eventobj.eventcontent)

        elif MessageTypes.ROUTE_FORWARDING == message_type:
            route = eventobj.eventcontent.payload[0]
            next_component_id = self.get_next_component_id(route)

            if next_component_id is not None:
                self.send_unicast_message(next_component_id, eventobj.eventcontent)

            else:
                if self.get_component_id() == src:
                    broken_link = route[0:1]

                    header = GenericMessageHeader(MessageTypes.ROUTE_ERROR,
                                                  self.componentname + "-" + str(src),
                                                  self.componentname + "-" + str(src))

                    event = Event(self,
                                  EventTypes.MFRB,
                                  GenericMessage(header,
                                                 [route, broken_link]))

                    self.send_up(event)
                else:
                    new_src = self.get_component_id()
                    new_dst = src

                    try:
                        index_of_current_component = route.index(self.get_component_id())
                        new_route = route[0: index_of_current_component]

                        broken_link = [self.get_component_id(), next_component_id]

                        prev_component_id = self.get_prev_component_id(route)

                        header = GenericMessageHeader(MessageTypes.ROUTE_ERROR,
                                                      self.componentname + "-" + str(new_src),
                                                      self.componentname + "-" + str(new_dst))

                        event = Event(self,
                                      EventTypes.MFRT,
                                      GenericMessage(header,
                                                     [new_route, broken_link]))

                        if prev_component_id is not None:
                            self.send_unicast_message(prev_component_id, event.eventcontent)

                    except ValueError:
                        print(
                            "[DSRAlgorithmComponent:transmit_route_forwarding][Error] component_id not in the route")
                        print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] component_id = " +
                              str(self.get_component_id()))
                        str_route = ' '.join(map(str, route))
                        print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] route = " + str_route)

        else:
            print("Unknown MessageTypes = " + message_type)
