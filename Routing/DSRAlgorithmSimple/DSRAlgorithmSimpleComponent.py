import enum
import time

from Ahc import ComponentModel
from Ahc import Event
from Ahc import GenericMessage
from Ahc import GenericMessageHeader
from Ahc import EventTypes
from Ahc import ComponentRegistry
from Ahc import ConnectorTypes


class MessageTypes(enum.Enum):
    ROUTE_FORWARDING = "ROUTE_FORWARDING"
    ROUTE_ERROR = "ROUTE_ERROR"
    ROUTE_REPLY = "ROUTE_REPLY"
    ROUTE_REQUEST = "ROUTE_REQUEST"


class DSRAlgorithmSimpleComponent(ComponentModel):

    def __init__(self, component_name, componentinstancenumber):
        super(DSRAlgorithmSimpleComponent, self).__init__(component_name, componentinstancenumber)
        self.hop_limit = 9
        self.uid = 0
        self.trial_number = 3
        self.route_cache = {}
        self.route_req_cache = {}

    def on_init(self, event_obj: Event):
        if self.get_component_id() == 0:
            dst = len(ComponentRegistry.components) - 1
            self.start_data_sending(dst, "Data send by componentinstancenumber == 0")

    def get_component_id(self):
        return self.componentinstancenumber

    def is_source(self, src) -> bool:
        return src == self.get_component_id()

    def is_destination(self, dst) -> bool:
        return dst == self.get_component_id()

    def process_message(self, data):
        print(f"I am {self.componentname} {self.componentinstancenumber}, data={data}\n")

    def get_next_component_id(self, route):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_next_component = index_of_current_component + 1
            return route[index_of_next_component]
        except ValueError:
            print("[DSRAlgorithmComponent:get_next_component_id][Exception] ValueError")
            print("component_id = " + self.get_component_id())
            print("route = " + route)
            return None

    def get_prev_component_id(self, route):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_prev_component = index_of_current_component - 1
            return route[index_of_prev_component]
        except ValueError:
            print("[DSRAlgorithmComponent:get_prev_component_id][Exception] ValueError")
            print("component_id = " + self.get_component_id())
            print("route = " + route)
            return None

    def is_link_up(self, next_component_id) -> bool:
        if next_component_id in self.connectors[ConnectorTypes.PEER]:
            return True
        return False

    def create_event(self, message_type, src, dst, route, data=None) -> Event:
        message_header = GenericMessageHeader(message_type, src, dst)
        message_payload = [route, data]
        message = GenericMessage(message_header, message_payload)

        return Event(self, EventTypes.MFRP, message)

    def is_route_request_seen_before(self, src, uid) -> bool:
        if src in self.route_req_cache:
            if self.route_req_cache[src] >= uid:
                return True

        self.route_req_cache[src] = uid
        return False

    def is_destination_in_cache(self, dst) -> bool:
        if dst in self.route_cache:
            return True

        return False

    def get_route_from_cache(self, dst) -> list:
        return self.route_cache[dst]

    def create_unique_id_for_req(self):
        return self.uid + 1

    @staticmethod
    def get_current_time_in_ms():
        return round(time.time() * 1000)

    def wait_for_route_reply(self, dst):

        sleep_period_in_ms = 100
        sleep_period_in_sec = sleep_period_in_ms / 1000

        timeout_in_sec = 10
        timeout_in_ms = timeout_in_sec * 1000
        start_time_in_ms = self.get_current_time_in_ms()
        end_time_in_ms = start_time_in_ms + timeout_in_ms

        # overflow check in time
        while end_time_in_ms > self.get_current_time_in_ms():
            if self.is_destination_in_cache(dst):
                return

            time.sleep(sleep_period_in_sec)

    def start_route_discovery(self, dst):
        src = self.get_component_id()
        route = [src]
        uid = self.create_unique_id_for_req()

        self.transmit_route_request(src, dst, route, uid)
        self.wait_for_route_reply(dst)

    def start_route_maintenance(self, dst):
        self.start_route_discovery(dst)

    def start_data_sending(self, dst, data):

        for i in range(self.trial_number):

            if self.is_destination_in_cache(dst):

                src = self.get_component_id()
                route = self.get_route_from_cache(dst)

                self.transmit_route_forwarding(src, dst, route, data)
                return

            # waits in start_route_discovery
            self.start_route_discovery(dst)

    def on_message_from_peer(self, event_obj: Event):

        src = event_obj.eventcontent.header.messagefrom
        dst = event_obj.eventcontent.header.messageto
        [route, data] = event_obj.eventcontent.payload

        uid = broken_link = data

        message_type = event_obj.eventcontent.header.messagetype
        if MessageTypes.ROUTE_FORWARDING == message_type:
            self.receive_route_forwarding(src, dst, route, data)

        elif MessageTypes.ROUTE_ERROR == message_type:
            self.receive_route_error(src, dst, route, broken_link)

        elif MessageTypes.ROUTE_REPLY == message_type:
            self.receive_route_reply(src, dst, route)

        elif MessageTypes.ROUTE_REQUEST == message_type:
            self.receive_route_request(src, dst, route, uid)

    def receive_route_forwarding(self, src, dst, route, data):
        if self.is_destination(dst):
            self.process_message(data)
        else:
            self.transmit_route_forwarding(src, dst, route, data)

    def receive_route_error(self, src, dst, route, broken_link):

        # delete from cache
        if self.is_destination(dst):
            self.start_route_maintenance(dst)
        else:
            self.transmit_route_error(src, dst, route, broken_link)

    def receive_route_reply(self, src, dst, route):
        # cache
        if not self.is_destination(dst):
            self.transmit_route_reply(src, dst, route)

    def receive_route_request(self, src, dst, route, uid):

        if self.is_route_request_seen_before(src, uid):
            pass
        elif self.is_destination(dst):
            route.append(self.get_component_id())
            new_src = dst
            new_dst = src
            # add to cache
            self.transmit_route_reply(new_src, new_dst, route)

        elif self.is_destination_in_cache(dst):
            # add to cache
            rest_of_the_route = self.get_route_from_cache(dst)
            route.append(rest_of_the_route)
            new_src = dst
            new_dst = src
            self.transmit_route_reply(new_src, new_dst, route)

        elif self.is_source(src):
            pass
        elif self.get_component_id() in route:
            pass
        else:
            if len(route) < self.hop_limit:
                route.append(self.get_component_id())
                # add to cache
                self.transmit_route_request(src, dst, route, uid)

    def transmit_route_forwarding(self, src, dst, route, data):
        next_component_id = self.get_next_component_id(route)

        if (next_component_id is not None) and (self.is_link_up(next_component_id)):

            event = self.create_event(MessageTypes.ROUTE_FORWARDING, src, dst, route, data)

            next_component = ComponentRegistry.getComponentByKey(self.componentname, next_component_id)
            if next_component:
                next_component.trigger_event(event)

        else:
            if self.is_source(src):
                broken_link = route[0:1]
                self.receive_route_error(src, src, route, broken_link)
            else:
                new_src = self.get_component_id()
                new_dst = src

                try:
                    index_of_current_component = route.index(self.get_component_id())
                    new_route = route[0: index_of_current_component]

                    broken_link = [self.get_component_id(), next_component_id]
                    self.transmit_route_error(new_src, new_dst, new_route, broken_link)

                except ValueError:
                    print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] component_id not in the route")
                    print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] component_id = " +
                          self.get_component_id())
                    print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] route = " + route)

    def transmit_route_error(self, src, dst, route, broken_link):
        prev_component_id = self.get_prev_component_id(route)

        if (prev_component_id is not None) and (self.is_link_up(prev_component_id)):

            event = self.create_event(MessageTypes.ROUTE_ERROR, src, dst, route, broken_link)

            prev_component = ComponentRegistry.getComponentByKey(self.componentname, prev_component_id)
            if prev_component:
                prev_component.trigger_event(event)

    def transmit_route_reply(self, src, dst, route):
        prev_component_id = self.get_prev_component_id(route)

        if (prev_component_id is not None) and (self.is_link_up(prev_component_id)):

            event = self.create_event(MessageTypes.ROUTE_REPLY, src, dst, route)

            prev_component = ComponentRegistry.getComponentByKey(self.componentname, prev_component_id)
            if prev_component:
                prev_component.trigger_event(event)

    def transmit_route_request(self, src, dst, route, uid):

        event = self.create_event(MessageTypes.ROUTE_REQUEST, src, dst, route, uid)
        self.send_peer(event)
