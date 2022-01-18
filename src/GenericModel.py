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
  
    def __init__(self) -> None:
        pass


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
