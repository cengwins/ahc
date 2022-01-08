import threading
import time
from collections import Counter
from enum import Enum

# total message count
# lsu message count (routing overhead)
# app message count
# link change count
# packet delivery ratio
# path optimality


class STARStatEvent(Enum):
    MSG_SENT = "MessageSent"
    LSU_MSG_SENT = "LSUMessageSent"
    LSU_MSG_RECV = "LSUMessageSent"
    APP_MSG_SENT = "AppMessageSent"
    APP_MSG_RECV = "AppMessageReceived"
    LINK_UPDATED = "LinkUpdated"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


class STARStats(object):
    def __init__(self):
        self.msg_sent = 0
        self.lsu_sent = 0
        self.lsu_recv = 0
        self.app_sent = 0
        self.app_recv = 0
        self.link_updated = 0

        self._lock = threading.Lock()
        self.handlers = {
            STARStatEvent.LSU_MSG_SENT: self.on_lsu_sent,
            STARStatEvent.LSU_MSG_RECV: self.on_lsu_recv,
            STARStatEvent.APP_MSG_SENT: self.on_app_msg_sent,
            STARStatEvent.APP_MSG_RECV: self.on_app_msg_recv,
            STARStatEvent.LINK_UPDATED: self.on_link_updated
        }

    def emit(self, event_type: STARStatEvent, data=None):
        if event_type in self.handlers.keys():
            self.handlers[event_type](data)

    def on_lsu_sent(self, data):
        with self._lock:
            self.msg_sent += 1
            self.lsu_sent += 1

    def on_lsu_recv(self, data=1):
        with self._lock:
            self.msg_sent += 1
            self.lsu_recv += data

    def on_app_msg_sent(self, data):
        with self._lock:
            self.msg_sent += 1
            self.app_sent += 1

    def on_app_msg_recv(self, data):
        with self._lock:
            self.app_recv += 1

    def on_link_updated(self, data):
        with self._lock:
            self.link_updated += 1

    def get_stats(self):
        with self._lock:
            data = {
                STARStatEvent.MSG_SENT: self.msg_sent,
                STARStatEvent.LSU_MSG_SENT: self.lsu_sent,
                STARStatEvent.LSU_MSG_RECV: self.lsu_recv,
                STARStatEvent.APP_MSG_SENT: self.app_sent,
                STARStatEvent.APP_MSG_RECV: self.app_recv,
                STARStatEvent.LINK_UPDATED: self.link_updated,
            }

            self.msg_sent = 0
            self.lsu_sent = 0
            self.lsu_recv = 0
            self.app_sent = 0
            self.app_recv = 0
            self.link_updated = 0

        return data


class MessageGenerator:
    def __init__(self, mps=1, sender_fn=None):
        """
        mps: Number of messages per second
        sender_fn: Function to be called
        """
        durations = [1, 2, 4, 8]
        self.mps = mps if mps in durations else 1
        self.sleep_time: float = 1.0 / self.mps
        self.sender_fn = sender_fn
        self.terminated = False

    def terminate(self):
        self.terminated = True

    def start(self):
        self.terminated = False

        while not self.terminated:
            self.sender_fn()
            time.sleep(self.sleep_time)
