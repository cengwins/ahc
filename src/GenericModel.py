import queue
from typing import Dict
from typing import ClassVar, Generic
from helpers import *
from generics import *
from definitions import *
from topology import *
from threading import Thread, Lock
from random import sample
from OSIModel import *
import GenericEvent


class GenericModel:

    connectors: Dict = {}
    terminated = False

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1):
        self.context = context
        self.configurationparameters = configurationparameters
        self.eventhandlers = {EventTypes.INIT: self.on_init, EventTypes.MFRB: self.on_message_from_bottom,
                            EventTypes.MFRT: self.on_message_from_top, EventTypes.MFRP: self.on_message_from_peer}
        # Add default handlers to all instantiated components.
        # If a component overwrites the __init__ method it has to call the super().__init__ method
        self.inputqueue = queue.Queue()
        self.componentname = componentname
        self.componentinstancenumber = componentinstancenumber
        self.num_worker_threads = num_worker_threads
        try:
            if self.connectors:
                pass
        except AttributeError:
            self.connectors = ConnectorList()


        #TODO: Handle This Part 
        # for i in range(self.num_worker_threads):
        #     t = Thread(target=self.queue_handler, args=[self.inputqueue])
        #     t.daemon = True
        #     t.start()

        # self.registry = ComponentRegistry()
        # self.registry.add_component(self)


    def send_down(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.DOWN]:
                p.trigger_event(event)
        except:
            pass

    def send_up(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.UP]:
                p.trigger_event(event)
        except:
            pass

    def send_peer(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.PEER]:
                p.trigger_event(event)
        except:
            pass

    def connect_me_to_component(self, name, component):
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component
    
    def on_message_from_bottom(self, eventobj: Event):
        print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_peer(self, eventobj: Event):
        print(f"{EventTypes.MFRP}  {self.componentname}.{self.componentinstancenumber}")
