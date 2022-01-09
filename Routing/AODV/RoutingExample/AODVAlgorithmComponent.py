#!/usr/bin/env python
"""
    Implementation of the AODV Routing Algorithm.
"""

__author__ = "Semih Kurt"
__contact__ = "semikurt@gmail.com"
__copyright__ = "Copyright 2022, WINSLAB"
__credits__ = ["Semih Kurt"]
__date__ = "2022/01/05"
__deprecated__ = False
__email__ = "semikurt@gmail.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

import os
import sys
import time
import random

sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels.Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer


class RoutingAODVComponent(ComponentModel):
    def __init__(self,componentname,componentid):
        super().__init__(componentname,componentid)

    def on_init(self, eventobj: Event):
        super().on_init(eventobj)
        
    def on_message_from_bottom(self,eventobj: Event):
        print(f"{self.componentinstancenumber} received {message_destination}")
        
