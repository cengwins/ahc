import enum
import time

from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry


class MessageTypes(enum.Enum):
    ROUTE_REQUEST = "ROUTE_REQUEST"
    ROUTE_REPLY = "ROUTE_REPLY"


class DSRAlgorithmComponent(ComponentModel):
    hop_limit = 99
    trial_number = 3

    def __init__(self, component_name, componentinstancenumber):
        super(DSRAlgorithmComponent, self).__init__(component_name, componentinstancenumber)
        self.cache = {}

    # def on_init(self, event_obj: Event):
    #     if self.componentinstancenumber == 0:
    #         evt = Event(self, EventTypes.MFRP, "first node to all peers")
    #         self.send_peer(evt)

    def on_message_from_peer(self, eventobj: Event):
        message_type = eventobj.eventcontent.header.messagetype

        if MessageTypes.ROUTE_REQUEST == message_type:
            pass
        elif MessageTypes.ROUTE_REPLY == message_type:
            pass

    def get(self):
        pass

    def send(self, data, path) -> bool:
        # maintenance here
        pass

    def send_route_req(self, src, dest, path, hop_limit):

        message_header = GenericMessageHeader(MessageTypes.ROUTE_REQUEST,
                                              src,
                                              dest)
        message_payload = path
        message = GenericMessage(message_header, message_payload)

        event = Event(self, EventTypes.MFRP, message)
        self.send_peer(event)

    @staticmethod
    def get_current_time_in_ms():
        return round(time.time() * 1000)

    def is_reply_received(self) -> bool:
        # when event triggered, this will be true
        pass

    def wait_for_route_reply(self) -> list:

        sleep_period_in_ms = 100
        sleep_period_in_sec = sleep_period_in_ms / 1000

        timeout_in_sec = 10
        timeout_in_ms = timeout_in_sec * 1000
        start_time = self.get_current_time_in_ms()
        end_time = start_time + timeout_in_ms

        while end_time > self.get_current_time_in_ms():
            if self.is_reply_received():
                return ["add_reply_here"]

            time.sleep(sleep_period_in_sec)

        return []

    def start_route_discovery(self, dest) -> list:
        path = [self.componentinstancenumber]
        self.send_route_req(self.componentinstancenumber, dest, path, self.hop_limit)
        return self.wait_for_route_reply()

    def send_data(self, data, dest):

        for i in range(self.trial_number):

            path = self.cache[dest]
            if not path:
                path = self.start_route_discovery(dest)
                self.cache[dest] = path

            if path:
                if self.send(data, path):
                    return
                else:
                    self.cache[dest] = []

    def send_route_reply(self, src, dest, path: list):

        nexthop = -1
        for i in range(len(path)):
            if path[i] == self.componentinstancenumber:
                if i > 0:  # i cannot be zero bcs zero index for src
                    nexthop = path[i - 1]

        message_header = GenericMessageHeader(MessageTypes.ROUTE_REPLY,
                                              src,
                                              dest,
                                              nexthop)
        message_payload = path
        message = GenericMessage(message_header, message_payload)

        event = Event(self, EventTypes.MFRP, message)

        component_to_send = ComponentRegistry.getComponentByKey(self.componentname, nexthop)
        component_to_send.trigger_event(event)

    def get_route_req(self, src, dest, path, hop_limit):

        if self.componentinstancenumber == dest:
            path.append(self.componentinstancenumber)
            new_src = dest
            new_dest = src
            self.send_route_reply(new_src, new_dest, path)

        elif self.cache[dest]:
            rest_of_the_path = self.cache[dest]
            path.append(rest_of_the_path)
            new_src = dest
            new_dest = src
            self.send_route_reply(new_src, new_dest, path)

        elif self.componentinstancenumber == src:
            pass

        elif self.componentinstancenumber in path:
            pass

        else:
            if hop_limit > 1:
                path.append(self.componentinstancenumber)
                self.send_route_req(src, dest, path, hop_limit - 1)
