import enum
import threading
import time

from Ahc import ComponentModel
from Ahc import ComponentRegistry
from Ahc import ConnectorTypes
from Ahc import Event
from Ahc import EventTypes
from Ahc import GenericMessage
from Ahc import GenericMessageHeader
from Ahc import Thread


class MessageTypes(enum.Enum):
    ROUTE_FORWARDING = "ROUTE_FORWARDING"
    ROUTE_ERROR = "ROUTE_ERROR"
    ROUTE_REPLY = "ROUTE_REPLY"
    ROUTE_REQUEST = "ROUTE_REQUEST"


class Cache:

    def __init__(self):
        self.lock = threading.RLock()
        self.cache = {}

    def has(self, key) -> bool:
        with self.lock:

            if key in self.cache:
                return True

            return False

    def get_value(self, key):
        with self.lock:

            if self.has(key):
                return None
            else:
                value = self.cache[key]
                return value

    def set_value(self, key, value):
        with self.lock:

            self.cache[key] = value

    def delete_key(self, key):
        with self.lock:

            self.cache.pop(key, None)

    def has_same_value(self, key, value) -> bool:
        with self.lock:

            if self.has(key):
                return value == self.cache[key]
            else:
                return False

    def delete_keys_with_link(self, link):
        with self.lock:

            for key in list(self.cache.keys()):
                value = self.cache[key]
                if value.count(link[0]) > 0 and value.count(link[1]) > 0:
                    if value.index(link[0]) + 1 == value.index(link[1]):
                        self.delete_key(key)


class DSRAlgorithmComponent(ComponentModel):

    def __init__(self, component_name: str, componentinstancenumber: int):
        super(DSRAlgorithmComponent, self).__init__(component_name, componentinstancenumber)
        self.hop_limit = 9
        self.uid = 0
        self.trial_number = 3
        self.route_cache = Cache()
        self.route_request_table = Cache()

    def on_init(self, event_obj: Event):
        if self.get_component_id() == 0:
            last_components_id = len(ComponentRegistry.components) - 1
            thread = Thread(target=self.start_data_sending,
                            args=[last_components_id, "Data send by componentinstancenumber == 0"])
            thread.start()

    def is_destination(self, dst: int) -> bool:
        return dst == self.get_component_id()

    def is_link_up(self, next_component_id: int) -> bool:
        if next_component_id in self.connectors[ConnectorTypes.PEER]:
            return True
        return False

    def is_route_request_seen_before(self, src: int, uid: int) -> bool:

        if self.route_request_table.has(src):
            latest_uid = self.route_request_table.get_value(src)
            if latest_uid >= uid:
                return True

        self.route_request_table.set_value(src, uid)
        return False

    def is_source(self, src: int) -> bool:
        return src == self.get_component_id()

    def get_component_id(self) -> int:
        return self.componentinstancenumber

    @staticmethod
    def get_current_time_in_ms():
        return round(time.time() * 1000)

    def get_next_component_id(self, route: list):
        try:
            index_of_current_component = route.index(self.get_component_id())
            index_of_next_component = index_of_current_component + 1
            return route[index_of_next_component]
        except ValueError:
            print("[DSRAlgorithmComponent:get_next_component_id][Exception] ValueError")
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
            print("[DSRAlgorithmComponent:get_prev_component_id][Exception] ValueError")
            print("component_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("route = " + str_route)
            return None

    def create_event(self, message_type, src: int, dst: int, route: list, data=None) -> Event:
        message_header = GenericMessageHeader(message_type, src, dst)
        message_payload = [route, data]
        message = GenericMessage(message_header, message_payload)

        return Event(self, EventTypes.MFRP, message)

    def create_unique_id_for_req(self) -> int:
        return self.uid + 1

    def process_message(self, data: str) -> None:
        print(f"I am {self.componentname} {self.componentinstancenumber}, data={data}\n")

    def start_data_sending(self, dst: int, data) -> None:

        for i in range(self.trial_number):

            if self.route_cache.has(dst):
                src = self.get_component_id()
                route = self.route_cache.get_value(dst)

                self.transmit_route_forwarding(src, dst, route, data)
                return

            # waits in start_route_discovery
            self.start_route_discovery(dst)

    def start_route_discovery(self, dst: int) -> None:
        src = self.get_component_id()
        route = [src]
        uid = self.create_unique_id_for_req()

        self.transmit_route_request(src, dst, route, uid)
        self.wait_for_route_reply(dst)

    def start_route_maintenance(self, dst: int) -> None:
        self.start_route_discovery(dst)

    def wait_for_route_reply(self, dst: int) -> None:

        sleep_period_in_ms = 100
        sleep_period_in_sec = sleep_period_in_ms / 1000

        timeout_in_sec = 10
        timeout_in_ms = timeout_in_sec * 1000
        start_time_in_ms = self.get_current_time_in_ms()
        end_time_in_ms = start_time_in_ms + timeout_in_ms

        # overflow check in time
        while end_time_in_ms > self.get_current_time_in_ms():
            if self.route_cache.has(dst):
                return

            time.sleep(sleep_period_in_sec)

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

    def receive_route_forwarding(self, src: int, dst: int, route: list, data) -> None:
        if self.is_destination(dst):
            self.process_message(data)
        else:
            self.transmit_route_forwarding(src, dst, route, data)

    def receive_route_error(self, src: int, dst: int, route: list, broken_link: list) -> None:

        self.route_cache.delete_keys_with_link(broken_link)

        if self.is_destination(dst):
            self.start_route_maintenance(dst)
        else:
            self.transmit_route_error(src, dst, route, broken_link)

    def receive_route_reply(self, src: int, dst: int, route: list) -> None:
        try:
            index_of_current_component = route.index(self.get_component_id())
            new_route = route[index_of_current_component:-1]

            if not self.route_cache.has(src):
                self.route_cache.set_value(src, new_route)
            elif len(new_route) < len(self.route_cache.get_value(src)):
                self.route_cache.set_value(src, new_route)

        except ValueError:
            print("[DSRAlgorithmComponent:get_next_component_id][Exception] ValueError")
            print("component_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("route = " + str_route)
            return None

        if not self.is_destination(dst):
            self.transmit_route_reply(src, dst, route)

    def receive_route_request(self, src: int, dst: int, route: list, uid: int) -> None:

        if self.is_route_request_seen_before(src, uid):
            pass
        elif self.is_destination(dst):
            route.append(self.get_component_id())
            new_src = dst
            new_dst = src

            if not self.route_cache.has(src):
                self.route_cache.set_value(src, route[::-1])
            elif len(route) < len(self.route_cache.get_value(src)):
                self.route_cache.set_value(src, route[::-1])

            self.transmit_route_reply(new_src, new_dst, route)

        elif self.route_cache.has(dst):

            if not self.route_cache.has(src):
                new_route = route
                new_route.append(self.get_component_id())
                self.route_cache.set_value(src, new_route[::-1])
            elif len(route) + 1 < len(self.route_cache.get_value(src)):
                new_route = route
                new_route.append(self.get_component_id())
                self.route_cache.set_value(src, new_route[::-1])

            rest_of_the_route = self.route_cache.get_value(dst)
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

                if not self.route_cache.has(src):
                    self.route_cache.set_value(src, route[::-1])
                elif len(route[::-1]) < len(self.route_cache.get_value(src)):
                    self.route_cache.set_value(src, route[::-1])

                self.transmit_route_request(src, dst, route, uid)

    def transmit_route_forwarding(self, src: int, dst: int, route: list, data) -> None:
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
                          str(self.get_component_id()))
                    str_route = ' '.join(map(str, route))
                    print("[DSRAlgorithmComponent:transmit_route_forwarding][Error] route = " + str_route)

    def transmit_route_error(self, src: int, dst: int, route: list, broken_link: list) -> None:
        prev_component_id = self.get_prev_component_id(route)

        if (prev_component_id is not None) and (self.is_link_up(prev_component_id)):

            event = self.create_event(MessageTypes.ROUTE_ERROR, src, dst, route, broken_link)

            prev_component = ComponentRegistry.getComponentByKey(self.componentname, prev_component_id)
            if prev_component:
                prev_component.trigger_event(event)

    def transmit_route_reply(self, src: int, dst: int, route: list) -> None:
        prev_component_id = self.get_prev_component_id(route)

        if (prev_component_id is not None) and (self.is_link_up(prev_component_id)):

            event = self.create_event(MessageTypes.ROUTE_REPLY, src, dst, route)

            prev_component = ComponentRegistry.getComponentByKey(self.componentname, prev_component_id)
            if prev_component:
                prev_component.trigger_event(event)

    def transmit_route_request(self, src: int, dst: int, route: list, uid: int) -> None:

        event = self.create_event(MessageTypes.ROUTE_REQUEST, src, dst, route, uid)
        self.send_peer(event)

