

import queue
from multiprocessing import Process, Queue, Pipe
import networkx as nx
from ..Generics import *
import time
import os, sys, signal


class NodeProcess(Process):
    def __init__(self,nodetype, componentinstancenumber, child_conn,node_queues=None, channel_queues=None):
        self.nodetype = nodetype
        self.componentinstancenumber = componentinstancenumber
        self.child_conn = child_conn
        self.node_queues = node_queues
        self.channel_queues = channel_queues
        super(NodeProcess,self).__init__()

    def ctrlc_signal_handler(self,sig, frame):
        #self.cc.exit_process()
        time.sleep(1)
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self.ctrlc_signal_handler)
        #self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None
        self.node = self.nodetype(self.nodetype.__name__, self.componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn = self.child_conn, node_queues=self.node_queues, channel_queues=self.channel_queues)
        polltime=0.00000001
        while(True):
            if self.child_conn.poll(polltime):
                ev:Event = self.child_conn.recv()
                match ev.event:
                    case EventTypes.INIT:
                        self.node.initiate_process()
                    case EventTypes.EXIT:
                        self.node.exit_process()
                        time.sleep(1) # For clearing up the exit events of components
                        return
                    case _:
                        self.node.trigger_event(ev)
            # probe queues from channels
            dest = int(self.componentinstancenumber)
            if self.node_queues is not None:
                number_of_nodes = len(self.node_queues[0])
                for i in range(number_of_nodes):
                    src = i
                    try:
                        if self.node_queues[dest][src] is not None:
                            ev = self.node_queues[src][dest].get(block=True, timeout=polltime)
                            self.node.trigger_event(ev)
                    except queue.Empty:
                        pass
                    except Exception as ex:
                        logger.critical(f"Exception in LogicalChannelProcess {ex}")
                        pass
