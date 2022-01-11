import os
import sys
sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology
import time
import numpy as np


class FisheyeZoneRoutingProtocolComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        print("Hello World1")
        super(FisheyeZoneRoutingProtocolComponent, self).__init__(componentname, componentid)
        print("Hello World2")
        self.queue_lock = Lock()
        self.message_queue = []
        print("Hello World3")

        self.basicZone = []
        self.extendedZone = []
        print("Hello World4")

    def on_init(self, eventobj: Event):
        print("Hello World5")
        super(FisheyeZoneRoutingProtocolComponent, self).on_init(eventobj)
        print("Hello World6")

        thread = Thread(target=self.job, args=[45, 54, 123])
        thread.start()
        print("Hello World7")
