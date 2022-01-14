import time

from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, \
    Topology
from enum import Enum
import datetime
import threading
from ahc.Routing.CGSR.CGSR import RouteRequestPacket, RREPPacket, SourceRouting, HelloMessage, ClusterAdjacencyExtension, CGSREventTypes, \
    CGSRMessageType
import random


class CGSRControlThread(threading.Thread):
    def __init__(self, event, interval, unique_name, component):
        threading.Thread.__init__(self)
        self.stopped = event
        self.increment = 0
        self.increment2 = 0
        self.interval = interval
        self.unique_name = unique_name
        self.component = component
        self.wakeup=True

    def run(self):
        if self.wakeup is True:
            time.sleep(2)
        while not self.stopped.wait(1):
            self.wakeup=False
            # print(f"control thread for node {self.unique_name} has started")
            self.increment += 1
            if self.increment == 2:
                self.component.generate_hello()

            if self.increment == 4:
                self.component.generate_hello()
                self.component.generate_rreq()
                self.increment = 0


class CGSRControlComponent(ComponentModel):

    def __init__(self, componentname, componentid):
        super(CGSRControlComponent, self).__init__(componentname, componentid)
        self.C_TIMER = 4
        self.U_TIMER = 3
        self.HELLO_INTERVAL = 2
        self.MAX_JITTER = self.HELLO_INTERVAL / 4
        self.JITTER = round(random.uniform(0, self.MAX_JITTER))
        self.RANDOM_HELLO_INTERVAL = self.HELLO_INTERVAL - self.MAX_JITTER

        self.timer = threading.Event()
        self.control_thread = CGSRControlThread(self.timer, self.RANDOM_HELLO_INTERVAL, self.unique_name(), self)
        self.send_self(Event(self, EventTypes.INIT, None))

    def on_init(self, eventobj: Event):
        super(CGSRControlComponent, self).on_init(eventobj)
        #print('control thread started')

        self.control_thread.start()

    def generate_hello(self):
        self.send_peer(Event(self, EventTypes.MFRP, CGSRMessageType.GENERATE_HELLO))
        # print('generate hello')

    def generate_rreq(self):
        self.send_peer(Event(self, EventTypes.MFRP, CGSRMessageType.GENERATE_RREQ))
