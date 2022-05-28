
import queue
from multiprocessing import Process, Queue, Pipe
import networkx as nx
from ..Generics import *
import time
import os, sys, signal


class LogicalChannelProcess(Process):
	def __init__(self,channeltype, componentinstancenumber, child_conn,  node_queues, channel_queues):
		self.channeltype = channeltype
		self.componentinstancenumber = componentinstancenumber
		self.src = int(self.componentinstancenumber.split("-")[0])
		self.dest = int(self.componentinstancenumber.split("-")[1])
		self.child_conn = child_conn
		self.node_queues = node_queues
		self.channel_queues = channel_queues
		super(LogicalChannelProcess,self).__init__()

	def ctrlc_signal_handler(self,sig, frame):
		#self.cc.exit_process()
		time.sleep(1)
		sys.exit(0)

	def run(self):
		signal.signal(signal.SIGINT, self.ctrlc_signal_handler)
		self.ch = self.channeltype(self.channeltype.__name__, self.componentinstancenumber,child_conn=self.child_conn, node_queues=self.node_queues, channel_queues=self.channel_queues)
		polltime=0.00001
		while(True):
			if self.child_conn.poll(polltime):
				ev:Event = self.child_conn.recv()
				match ev.event:
					case EventTypes.INIT:
						self.ch.initiate_process()
					case EventTypes.EXIT:
						self.ch.exit_process()
						time.sleep(1) # For clearing up the exit events of components
						return
					case _:
						self.ch.trigger_event(ev)
			if self.channel_queues[self.src][self.dest] is not None:
				try:
					ev:Event = self.channel_queues[self.src][self.dest].get(block=True, timeout=polltime)
					if ev is not None:
						self.ch.trigger_event(ev)
				except queue.Empty:
					pass
				except Exception as ex:
					logger.critical(f"Exception in LogicalChannelProcess {ex}")
					pass      
