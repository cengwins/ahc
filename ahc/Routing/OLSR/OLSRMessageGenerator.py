import random
import time
from ahc.Ahc import ComponentModel, Event, EventTypes
import threading
from ahc.Routing.OLSR.OLSRSimplifiedComponent import OLSRMessageTypes
# TODO Not a proper implementations

class OLSRControlThread(threading.Thread):
    def __init__(self, event, component):
        threading.Thread.__init__(self)
        self.stopped = event
        self.increment = 0
        self.component = component
        self.wakeup = True

    def run(self):
        if self.wakeup is True:
            time.sleep(2)
        while not self.stopped.wait(1):
            self.wakeup = False
            self.increment += 1
            if self.increment == 2:
                self.component.generate_hello()

            if self.increment == 4:
                self.component.generate_hello()
                self.component.generate_tc()
                self.component.update_routing_table()
                self.increment = 0


class OLSRControlComponent(ComponentModel):

    def __init__(self, componentname, componentid):
        super(OLSRControlComponent, self).__init__(componentname, componentid)
        self.timer = threading.Event()
        self.control_thread = OLSRControlThread(self.timer, self).start()
        self.send_self(Event(self, EventTypes.INIT, None))

    def on_init(self, eventobj: Event):
        super(OLSRControlComponent, self).on_init(eventobj)
        # self.control_thread.start()

    def generate_hello(self):
        self.send_peer(Event(self, EventTypes.MFRP, OLSRMessageTypes.GENERATE_HELLO))

    def generate_tc(self):
        self.send_peer(Event(self, EventTypes.MFRP, OLSRMessageTypes.GENERATE_TC))

    def update_routing_table(self):
        self.send_peer(Event(self, EventTypes.MFRP, OLSRMessageTypes.UPDATE_TABLE))
