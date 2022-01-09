import os
import sys
sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology
import time
import numpy as np


class FisheyeZoneRoutingProtocolComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(FisheyeZoneRoutingProtocolComponent, self).__init__(componentname, componentid)
        self.queue_lock = Lock()
        self.message_queue = []
        if self.componentinstancenumber == 0:
            self.is_initiator = True
        else:
            self.is_initiator = False

        self.basicZone = []
        self.extendedZone = []

    def on_init(self, eventobj: Event):
        super(FisheyeZoneRoutingProtocolComponent, self).on_init(eventobj)
        if not self.is_initiator:
            thread = Thread(target=self.job, args=[45, 54, 123])
            thread.start()
