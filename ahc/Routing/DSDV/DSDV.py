'''
        This module is designed for the implementation of Distance Sequenced Distance Vector routing algorithm. In its paper,
    some parts are ambiguous. Therefore, some parts are decided by the developer itself.
'''

__author__ = "Bahadır Kisbet"
__contact__ = "bahadirkisbet@gmail.com"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Bahadır Kisbet"]
__date__ = "2021/04/07"  # will be updated later
__deprecated__ = False
__email__ = "bahadirkisbet@gmail.com"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Development"
__version__ = "0.0.1"

import sys
import os

sys.path.insert(0, os.getcwd())


import matplotlib.pyplot as plt
from enum import Enum
import numpy as np
import networkx as nx
from ahc.Ahc import (ComponentModel, Event, EventTypes, GenericMessage,
                 GenericMessageHeader, GenericMessagePayload, Topology)
import threading
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer
from ahc.Ahc import ConnectorTypes
from tabulate import tabulate
from time import sleep, time
import copy

# @TODO: Implement dynamically changing topology
class DSDVMessageTypes(Enum):
    '''
        INCREMENTAL_DUMP: It is a message which contains only the changes since the last broadcast
        FULL_DUMP: It is a message which contains all routing table. It is sent under specific conditions
    '''
    INCREMENTAL = "INCREMENTAL_DUMP"
    FULLDUMP = "FULL_DUMP"

class DSDVMessageHeader(GenericMessageHeader):
    def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), messagesource=-1, hopcount=0, sequencenumber=-1):
        super().__init__(messagetype, messagefrom, messageto, nexthop=nexthop, interfaceid=interfaceid, sequencenumber=sequencenumber)
        self.messagesource = messagesource
        self.hopcount = hopcount


class DSDVNode(ComponentModel): # It is an application layer
    def __init__(self,
        componentname: str,
        componentinstancenumber: str, 
        interval: float = 3.0,
        timeout: float = 7.0,
        expiration_time: int = 3, # if a node does not send a broadcast in interval, its expiration will increase by one. If it reaches to three, it will be accepted as broken link.
        verbose: bool = True) -> None:

        super().__init__(componentname=componentname, componentinstancenumber=componentinstancenumber)

        self.sequence_num = 0
        self.sequence_num_lock = threading.Lock()

        # every entry is -> destination: (nextHop, hopCount, seqnum)
        self.routing_table = {componentinstancenumber: (componentinstancenumber, 0, 0)} 
        self.lock = threading.Lock()

        self.incremental_table = copy.deepcopy(self.routing_table)
        self.incremental_table_lock = threading.Lock()

        self.cache = dict()
        self.cache_lock = threading.Lock()

        self.verbose = verbose
        self.log_table_path = f"ahc/Routing/DSDV/logs/graph2/log_table_{self.componentinstancenumber}.txt"
        self.log_throughput_path = f"ahc/Routing/DSDV/logs/graph2/log_throughput_{self.componentinstancenumber}.txt"
        
        self.expiration_dict = dict() # it keeps track of which neighbours havent send an update for expiration time
        self.expiration_lock = threading.Lock()

        self.timeout = timeout
        self._timer_(2, self._broadcast )
        self._timer_(3, self.print_routing_table)
        # self._timer_(interval, self.updateMsgToNeighbours)
        #threading.Timer(3.0, self.updateMsgToNeighbours).start()

    def _timer_(self, interval, function, *args):
        stopped = threading.Event()

        def loop():
            while not stopped.wait(interval): # the first call is in `interval` secs
                    function(*args)

        threading.Thread(target=loop).start()    
        return stopped.set
    
    def on_message_from_bottom(self, eventobj: Event):
        super().on_message_from_bottom(eventobj)

        header: GenericMessageHeader = eventobj.eventcontent.header
        payload: GenericMessagePayload = eventobj.eventcontent.payload

        if header.messagetype == DSDVMessageTypes.INCREMENTAL or header.messagetype == DSDVMessageTypes.FULLDUMP:
            self._handle_incremental(header, payload)

    def __increase_timeouts__(self) -> None:
        with self.expiration_lock:
            for entry in self.expiration_dict:
                self.expiration_dict[entry] += 1
   
    def print_routing_table(self) -> None:
        with self.lock, open(self.log_table_path, "a+") as f:
            headers = ["DESTINATION", "NEXT_HOP", "HOP_COUNT", "SEQ_NUM"]
            data = [ ",".join([str(entry)] + list(map(str,self.routing_table[entry]))) for entry in self.routing_table ]
            f.write(f"{time()}\n")
            f.write(str(self.componentinstancenumber) + "\n")
            f.write("\n".join(data))
            f.write('\n')

    ### NEW ###
    def _prepare_dump(self, to: int) -> GenericMessage:
        msg = None
        with self.lock:
            changes = dict()
            for element in self.routing_table:
                if element in self.incremental_table:
                    if self.routing_table[element] != self.incremental_table[element]:
                        changes[element] = self.routing_table[element]
                else:
                    changes[element] = self.routing_table[element]
            
            msg_type = DSDVMessageTypes.INCREMENTAL
            msg_payload = changes
            if len(changes) > len(self.routing_table) // 2:
                msg_type = DSDVMessageTypes.FULLDUMP
                msg_payload = self.routing_table

            header = DSDVMessageHeader(
                messagetype=msg_type,
                messagefrom=self.componentinstancenumber,
                messagesource=self.componentinstancenumber,
                hopcount=1,
                messageto=to,
                interfaceid=f"{self.componentinstancenumber}-{to}",
                nexthop=self.componentinstancenumber,
                sequencenumber=self.sequence_num
            )
            payload = GenericMessagePayload(msg_payload)
            msg = GenericMessage(header, payload)
        return msg

    def _prepare_message(self, to: int) -> GenericMessage:
        return self._prepare_dump(to)

    def _broadcast(self, msg: GenericMessage = None, is_mine = True) -> None:
        if is_mine:
            with self.sequence_num_lock, self.lock:
                self.sequence_num += 1
                self.routing_table[self.componentinstancenumber] = (self.componentinstancenumber, 0, self.sequence_num)
        
        packet = msg
        for neighbour in Topology().get_neighbors(self.componentinstancenumber):

            if msg == None:
                packet = self._prepare_message(neighbour)

            with open(self.log_throughput_path, "a+") as f:
                f.write(f"{time()}\t{sys.getsizeof(packet)}\n")
            self.send_down(Event(self, EventTypes.MFRT, packet))

    def _handle_incremental(self, header: DSDVMessageHeader, payload: GenericMessagePayload) -> None:
        with self.lock, self.cache_lock, self.expiration_lock:
            if header.messagefrom not in self.cache or self.cache[header.messagefrom] < header.sequencenumber:
                # The message is new
                self.cache[header.messagesource] = header.sequencenumber
                changes = payload.messagepayload
                
                others = dict() # it is a payload to send the broadcast to other nodes

                if header.messagesource not in self.routing_table:
                    self.routing_table[header.messagesource] = (header.messagefrom, header.hopcount, header.sequencenumber)

                if header.messagesource in self.expiration_dict: # it is cached before
                    curr_time = time()
                    self.expiration_dict[header.messagesource] = curr_time + self.timeout
                    for src in self.expiration_dict:
                        if self.expiration_dict[src] < curr_time:
                            self.routing_table[src] = (
                                self.routing_table[src][0],
                                float('inf'),
                                self.routing_table[src][0] + 1 )
                else:
                    self.expiration_dict[header.messagesource] = time() + self.timeout
                

                for change in changes:
                    if change in self.routing_table: # if it can be reachable from the source
                        #print(self.componentinstancenumber, change, self.routing_table[change][1], self.routing_table[header.messagesource][1] + changes[change][1])

                        if self.routing_table[change][1] >= self.routing_table[header.messagesource][1] + changes[change][1]:
                            # Bell-man Ford
                            if changes[change][-1] >= self.routing_table[change][-1]: # if the seqnum is more recent
                                self.routing_table[change] = (
                                    header.messagefrom,
                                    self.routing_table[header.messagesource][1] + changes[change][1],
                                    changes[change][-1])
                    else: # add to the routing table adding one hop count more
                        self.routing_table[change] = (
                            header.messagefrom,
                            changes[change][1] + 1,
                            changes[change][-1]
                        )
                    
                    others[change] = (
                            header.messagefrom,
                            changes[change][1],
                            changes[change][-1]
                        )
                header.messagefrom = self.componentinstancenumber
                header.hopcount += 1
                payload = GenericMessagePayload(others)
                #print(len(others), sys.getsizeof(others),sys.getsizeof(payload))
                self._broadcast(GenericMessage(header, payload), is_mine=False) # forward the packet
            else: # drop it
                pass


class AdHocNode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.applicationlayer   = DSDVNode("DSDVNode", componentid, 3.0)
        self.networklayer       = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer          = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.applicationlayer.connect_me_to_component(ConnectorTypes.DOWN, self.networklayer)
        self.networklayer.connect_me_to_component(ConnectorTypes.UP, self.applicationlayer)

        self.networklayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.networklayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

        super().__init__(componentname, componentid)


def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()

    #G = nx.random_geometric_graph(4, 0.5)
    # G = nx.Graph()
    # G.add_nodes_from([1,2,3,4,5,6,7,8,9,10,11,12])
    # G.add_edges_from([
    #     (1,2),
    #     (2,5),
    #     (3,4),
    #     (3,5),
    #     (4,5),
    #     (5,6),
    #     (6,7),
    #     (5,7),
    #     (5,8),
    #     (6,12),
    #     (7,10),
    #     (7,8),
    #     (8,9),
    #     (9,11),
    #     (10,11),
    #     (11,12)
    # ])
    G = nx.Graph()
    G.add_nodes_from([1,2,3,4])
    G.add_edges_from([
        (1,2),
        (1,3),
        (2,3),
        (2,4)
    ])

    nx.draw(G, with_labels=True, font_weight='bold')
    plt.draw()
    topo = Topology()
    topo.construct_from_graph(G, DSDVNode, P2PFIFOPerfectChannel, dynamic=False, path="/Users/bahadirkisbet/Desktop/projects/ahc/Routing/DSDV/logs/topology.txt")
    topo.start()
    sleep(15)
    exit(0)
    plt.show()
    #plt.show()



if __name__ == "__main__":
    main()
