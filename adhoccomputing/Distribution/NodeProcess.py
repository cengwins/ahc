

import queue
from multiprocessing import Process, Queue, Pipe
import networkx as nx
from ..Generics import *
import time
import os, sys, signal


class NodeProcess(Process):
    def __init__(self,nodetype, componentinstancenumber, child_conn,node_queues, channel_queues):
        self.nodetype = nodetype
        self.componentinstancenumber = componentinstancenumber
        self.child_conn = child_conn
        self.node_queues = node_queues
        self.channel_queues = channel_queues
        super(NodeProcess,self).__init__()

    def ctrlc_signal_handler(self,sig, frame):
        #print('You pressed Ctrl+C!')
        #self.cc.exit_process()
        time.sleep(1)
        sys.exit(0)

    def run(self):
        #print('module name:', __name__)
        #print('parent process:', os.getppid())
        #print('process id:', os.getpid())
        #print("NODEPROCESS-", self.componentinstancenumber, " started ", __name__, "ParentID ", os.getppid(), " SelfID", os.getpid() )
        signal.signal(signal.SIGINT, self.ctrlc_signal_handler)
        self.node = self.nodetype(self.nodetype.__name__, self.componentinstancenumber, child_conn = self.child_conn, node_queues=self.node_queues, channel_queues=self.channel_queues)
        polltime=0.00000001
        while(True):
            if self.child_conn.poll(polltime):
                ev:Event = self.child_conn.recv()
                #print("NODEPROCESS-", self.componentinstancenumber, " RECEIVED ", str(ev))
                match ev.event:
                    case EventTypes.INIT:
                        self.node.initiate_process()
                    case EventTypes.EXIT:
                        #print("EXITING: Node ", self.node.componentinstancenumber, os.getppid(), os.getpid())
                        self.node.exit_process()
                        time.sleep(1) # For clearing up the exit events of components
                        return
                    case _:
                        self.node.trigger_event(ev)
            # probe queues from channels
            dest = int(self.componentinstancenumber)
            if self.node_queues is not None:
                number_of_nodes = len(self.node_queues[0])
                #print("Will check node queues", self.dest, " for ", number_of_nodes)
                for i in range(number_of_nodes):
                    src = i
                    try:
                        if self.node_queues[dest][src] is not None:
                            ev = self.node_queues[src][dest].get(block=True, timeout=polltime)
                            #print( "\033[92mNODEPROCESS\033[0m",self.componentinstancenumber, " received ", str(ev))
                            self.node.trigger_event(ev)
                    except queue.Empty:
                        pass
                    except Exception as ex:
                        print("Exception in polling queues: ", ex)
                        pass
