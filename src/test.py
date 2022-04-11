import random
import threading
import time
import random

from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from Topology import Topology
from GenericModel import GenericModel
from GenericChannel import FIFOBroadcastPerfectChannel
from generics import *
from GenericEvent import *
from Broadcasting import ControlledFlooding

NETWORK_SIZE = 15
NETWORK_RADIUS = 0.8

BP = 1 # 1 second

DEFAULT_DELAY = 15


class TSFLayerMessageTypes(Enum):
	BEACONMESSAGE = "BEACONMESSAGE"


class TSFLayerMessageHeader(GenericMessageHeader):
	def __init__(self, *args, **kwargs):
		super().__init__(TSFLayerMessageTypes.BEACONMESSAGE, *args, **kwargs)


class TSFLayerMessagePayload(GenericMessagePayload):
	pass


class TSFLayerMessage(GenericMessage):
	pass


class TSFLayer(GenericModel):
	def __init__(self, componentname, componentinstancenumber):
		super().__init__(componentname, componentinstancenumber)

		self.lock = threading.Lock()

		self.beacon_timer_thread = None

		self.timer = random.randint(0, 1000)
		self.timer_lock = threading.Lock()

		thread = threading.Thread(target=self.inc_timer, args=[])
		thread.daemon = True
		thread.start()

		printer_thread = threading.Thread(target=self.print_counter, args=[])
		printer_thread.daemon = True
		# printer_thread.start()

		bp_thread = threading.Thread(target=self.run_bp, args=[])
		bp_thread.daemon = True
		bp_thread.start()

	def on_message_from_bottom(self, eventobj: Event):
		self.lock.acquire()

		if self.beacon_timer_thread is not None:
			self.timer_lock.acquire()

			if self.timer < eventobj.eventcontent.payload.messagepayload + DEFAULT_DELAY:
				self.timer = eventobj.eventcontent.payload.messagepayload + DEFAULT_DELAY

			self.timer_lock.release()


			self.beacon_timer_thread.cancel()
			self.beacon_timer_thread = None

		self.lock.release()

	def print_counter(self):
		time.sleep(0.1)

		while True:
			print(self.timer)
			time.sleep(0.1)

	def inc_timer(self):
		time.sleep(0.001)

		while True:
			self.timer_lock.acquire()
			self.timer += 1
			self.timer_lock.release()

			time.sleep(0.001)

	def run_bp(self):
		time.sleep(BP)

		while True:
			delay = random.uniform(0.0, 0.1)

			self.lock.acquire()

			self.beacon_timer_thread = threading.Timer(delay, self.send_beacon)
			self.beacon_timer_thread.start()

			self.lock.release()

			time.sleep(BP)

	def send_beacon(self):
		header = TSFLayerMessageHeader(self.componentinstancenumber, MessageDestinationIdentifiers.NETWORKLAYERBROADCAST)
		payload = TSFLayerMessagePayload(self.timer)

		message = TSFLayerMessage(header, payload)

		self.send_down(Event(self, EventTypes.MFRT, message))


class OzansNode(AdHocNode):
	def __init__(self, componentname, componentinstancenumber):
		super().__init__(componentname, componentinstancenumber)

		self.application_layer = TSFLayer('TSFLayer', componentinstancenumber)
		self.broadcast_service = ControlledFlooding('ControlledFlooding', componentinstancenumber)
		self.network_layer = GenericNetworkLayer('SimpleFlooding', componentinstancenumber)

	def on_message_from_top(self, eventobj: Event):
		self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

	def on_message_from_bottom(self, eventobj: Event):
		self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))


def time_diff():
	while True:
		components = []

		timers = []

		for component in components:
			timers.append(component.timer)

		avg = sum(timers) / len(timers) if len(timers) > 0 else 0
		result = 0

		for value in timers:
			result += abs(value - avg)

		result = result / len(timers) if len(timers) > 0 else 0
		print (result)

		time.sleep(0.01)

def main():
    G = nx.random_geometric_graph(NETWORK_SIZE, NETWORK_RADIUS)
  

    topology = Topology()
    topology.construct_from_graph(G, AdHocNode, FIFOBroadcastPerfectChannel)
    nodes  = list(topology.nodes)
    args = {}

    for i in nodes: 
      args['componentinstancenumber'] = topology.nodes[i].componentinstancenumber
      args['componentname'] =  topology.nodes[i].componentname
      args['topo'] = G



    # ComponentRegistry.print_components()


    topology.start()

    time_diff_thread = threading.Thread(target=time_diff, args=[])
    time_diff_thread.daemon = True
    time_diff_thread.start()

    topology.plot()
    plt.show()

    # while True:
    # 	time.sleep(1)

if __name__ == '__main__':
	main()
