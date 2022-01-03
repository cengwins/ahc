import enum
import threading
import time
from copy import deepcopy

from Ahc import ComponentModel
from Ahc import Event
from Ahc import EventTypes
from Ahc import GenericMessage
from Ahc import GenericMessageHeader
from Ahc import Thread

import logging

logging.basicConfig(filename="C:\\Users\\bsezgin\\Desktop\\newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


class MessageTypes(enum.Enum):
    ROUTE_FORWARDING = "ROUTE_FORWARDING"
    ROUTE_ERROR = "ROUTE_ERROR"
    ROUTE_REPLY = "ROUTE_REPLY"
    ROUTE_REQUEST = "ROUTE_REQUEST"


class Cache:

    def __init__(self, id):
        self.id = id
        self.lock = threading.RLock()
        self.cache = {}

    def has(self, key) -> bool:
        with self.lock:
            if key in self.cache:
                return True

            return False

    def get_value(self, key):
        with self.lock:

            if not self.has(key):
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

    def __init__(self, component_name, componentinstancenumber):
        super(DSRAlgorithmComponent, self).__init__(component_name, componentinstancenumber)
        self.hop_limit = 9
        self.uid = 0
        self.trial_number = 2
        self.route_cache = Cache(componentinstancenumber)
        self.route_request_table = Cache(componentinstancenumber)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    def is_destination(self, dst: int) -> bool:
        return dst == self.get_component_id()

    def is_route_request_seen_before(self, src: int, uid: int) -> bool:

        if self.route_request_table.has(src):
            latest_uid = self.route_request_table.get_value(src)
            if latest_uid is not None and latest_uid >= uid:
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

    def create_app_event(self, src: int, dst: int, data) -> Event:
        message_header = GenericMessageHeader("", self.componentname + "-" + str(src),
                                              self.componentname + "-" + str(dst))
        message_payload = data
        message = GenericMessage(message_header, message_payload)

        return Event(self, EventTypes.MFRB, message)

    def create_route_event(self, message_type, src: int, dst: int, route: list, data=None) -> Event:

        message_header = GenericMessageHeader(message_type, self.componentname + "-" + str(src),
                                              self.componentname + "-" + str(dst))

        new_route = deepcopy(route)
        message_payload = [new_route, data]
        message = GenericMessage(message_header, message_payload)

        return Event(self, EventTypes.MFRT, message)

    def create_unique_id_for_req(self) -> int:
        return self.uid + 1

    def start_data_sending(self, dst: int, data) -> None:

        for i in range(self.trial_number):

            if self.route_cache.has(dst):
                src = self.get_component_id()
                route = deepcopy(self.route_cache.get_value(dst))

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

        timeout_in_sec = 20
        timeout_in_ms = timeout_in_sec * 1000
        start_time_in_ms = self.get_current_time_in_ms()
        end_time_in_ms = start_time_in_ms + timeout_in_ms

        # overflow check in time
        while end_time_in_ms > self.get_current_time_in_ms():
            if self.route_cache.has(dst):
                return

            time.sleep(sleep_period_in_sec)

    def on_message_from_top(self, eventobj: Event):

        dst = int(eventobj.eventcontent.header.messageto.split("-")[1])
        data = eventobj.eventcontent.payload

        thread = Thread(target=self.start_data_sending, args=[dst, data])
        thread.start()

    def on_message_from_bottom(self, eventobj: Event):

        src = int(eventobj.eventcontent.header.messagefrom.split("-")[1])
        dst = int(eventobj.eventcontent.header.messageto.split("-")[1])
        # [route, data] = eventobj.eventcontent.payload[0]
        route = eventobj.eventcontent.payload[0]
        data = eventobj.eventcontent.payload[1]

        self.logger.debug("[DSR::bottom] id = " + str(self.get_component_id()) + " eventid = " + str(
            eventobj.eventid) + " route = " + str(route))

        uid = broken_link = data

        message_type = eventobj.eventcontent.header.messagetype
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
            event = self.create_app_event(src, dst, data)
            self.send_up(event)
        else:
            self.transmit_route_forwarding(src, dst, deepcopy(route), data)

    def receive_route_error(self, src: int, dst: int, route: list, broken_link: list) -> None:

        self.route_cache.delete_keys_with_link(deepcopy(broken_link))

        if self.is_destination(dst):
            self.start_route_maintenance(dst)
        else:
            self.transmit_route_error(src, dst, deepcopy(route), deepcopy(broken_link))

    def receive_route_reply(self, src: int, dst: int, route: list) -> None:
        try:
            index_of_current_component = route.index(self.get_component_id())
            new_route = route[index_of_current_component:]



            if not self.route_cache.has(src):
                self.route_cache.set_value(src, new_route)
            elif len(new_route) < len(self.route_cache.get_value(src)):
                self.route_cache.set_value(src, new_route)

            if self.get_component_id() == 0:
                print("Cache : " + str(self.route_cache.get_value(src)))

        except ValueError:
            print("[DSRAlgorithmComponent:receive_route_reply][Exception] ValueError")
            print("component_id = " + str(self.get_component_id()))
            str_route = ' '.join(map(str, route))
            print("route = " + str_route)
            return None

        if not self.is_destination(dst):
            self.transmit_route_reply(src, dst, deepcopy(route))

    def receive_route_request(self, src: int, dst: int, route: list, uid: int) -> None:

        id = self.get_component_id()
        self.logger.debug("[DSR::receive_route_request] id = " + str(id) + " route = " + str(route))
        if self.is_route_request_seen_before(src, uid):
            pass
        elif self.is_destination(dst):
            new_route = deepcopy(route)
            new_route.append(self.get_component_id())
            new_src = dst
            new_dst = src

            if not self.route_cache.has(src):
                self.route_cache.set_value(src, new_route[::-1])
            elif len(new_route) < len(self.route_cache.get_value(src)):
                self.route_cache.set_value(src, new_route[::-1])

            self.transmit_route_reply(new_src, new_dst, new_route)

        elif self.route_cache.has(dst):
            # buradaki routeları düzelt
            if not self.route_cache.has(src):
                new_route = route
                new_route.append(self.get_component_id())
                self.route_cache.set_value(src, new_route[::-1])
            elif len(route) + 1 < len(self.route_cache.get_value(src)):
                new_route = route
                new_route.append(self.get_component_id())
                self.route_cache.set_value(src, new_route[::-1])

            rest_of_the_route = deepcopy(self.route_cache.get_value(dst))
            route.append(rest_of_the_route)
            new_src = dst
            new_dst = src
            self.transmit_route_reply(new_src, new_dst, route)

        elif self.is_source(src):
            pass
        elif self.get_component_id() in route:
            pass
        else:
            new_route = deepcopy(route)
            self.logger.debug("[DSR::receive_route_request_2] id = " + str(id) + " route = " + str(new_route))
            if len(new_route) < self.hop_limit:
                new_route.append(self.get_component_id())

                self.logger.debug("[DSR::receive_route_request_3] id = " + str(id) + " route = " + str(new_route))

                if not self.route_cache.has(src):
                    self.route_cache.set_value(src, new_route[::-1])
                elif len(new_route[::-1]) < len(self.route_cache.get_value(src)):
                    self.route_cache.set_value(src, new_route[::-1])

                self.transmit_route_request(src, dst, new_route, uid)

    def transmit_route_forwarding(self, src: int, dst: int, route: list, data) -> None:
        event = self.create_route_event(MessageTypes.ROUTE_FORWARDING, src, dst, deepcopy(route), data)
        self.send_down(event)

    def transmit_route_error(self, src: int, dst: int, route: list, broken_link: list) -> None:
        event = self.create_route_event(MessageTypes.ROUTE_ERROR, src, dst, deepcopy(route), broken_link)
        self.send_down(event)

    def transmit_route_reply(self, src: int, dst: int, route: list) -> None:
        event = self.create_route_event(MessageTypes.ROUTE_REPLY, src, dst, deepcopy(route))
        self.send_down(event)

    def transmit_route_request(self, src: int, dst: int, route: list, uid: int) -> None:
        self.logger.debug(
            "[DSR::transmit_route_request] id = " + str(self.get_component_id()) + " route = " + str(route))
        print(str(Event.curr_event_id))
        event = self.create_route_event(MessageTypes.ROUTE_REQUEST, src, dst, deepcopy(route), uid)
        print(str(Event.curr_event_id))
        self.send_down(event)
