import threading
import time

from Ahc import singleton


@singleton
class DataCollector:

    def __init__(self):
        self._request_start_time = 0
        self._request_end_time = 0

        self._reply_start_time = 0
        self._reply_end_time = 0

        self._forwarding_start_time = 0
        self._forwarding_end_time = 0

        self._request_message_count = 0

        self._is_sim_ended = False

        self._is_req_msg_sent_recently = False

        self._found_route = []

        self._lock = threading.Lock()

        self._lock_2 = threading.Lock()

    def is_req_msg_sent_recently(self):
        with self._lock_2:
            return self._is_req_msg_sent_recently

    def set_req_msg_sent_recently(self, status: bool):
        with self._lock_2:
            self._is_req_msg_sent_recently = status

    def get_found_route(self):
        return self._found_route

    def set_found_route(self, route):
        self._found_route = route

    def is_sim_ended(self):
        return self._is_sim_ended

    def end_sim(self):
        self._is_sim_ended = True

    def get_request_message_count(self):
        return self._request_message_count

    def increase_request_message_count(self):
        with self._lock:
            self._request_message_count += 1

    @staticmethod
    def get_time_in_us():
        return time.time_ns() / (10 ** 3)

    def get_request_time_in_us(self):
        return self._request_end_time - self._request_start_time

    def start_request_timer(self):
        self._request_start_time = self.get_time_in_us()

    def end_request_timer(self):
        self._request_end_time = self.get_time_in_us()

    def get_reply_time_in_us(self):
        return self._reply_end_time - self._reply_start_time

    def start_reply_timer(self):
        self._reply_start_time = self.get_time_in_us()

    def end_reply_timer(self):
        self._reply_end_time = self.get_time_in_us()

    def get_forwarding_time_in_us(self):
        return self._forwarding_end_time - self._forwarding_start_time

    def start_forwarding_timer(self):
        self._forwarding_start_time = self.get_time_in_us()

    def end_forwarding_timer(self):
        self._forwarding_end_time = self.get_time_in_us()
