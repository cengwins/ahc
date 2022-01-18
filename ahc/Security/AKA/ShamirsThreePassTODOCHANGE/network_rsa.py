#!/usr/bin/env python
""" Implements the AHC library.

TODO: Longer description of this module to be written.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = "One solo developer"
__authors__ = ["Ertan Onur", "Özlem Tonkal", "etc"]
__contact__ = "eonur@ceng.metu.edu.tr"
__copyright__ = "Copyright 2021, WINSLAB"
__credits__ = ["Ertan Onur", "Özlem Tonkal", "etc"]
__date__ = "2022/01/14"
__deprecated__ = False
__email__ = "eonur@ceng.metu.edu.tr"
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.0.1"

import datetime
import time
import queue
from enum import Enum
from threading import Thread, Lock
from random import sample
import networkx as nx
import itertools

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key

inf = float('inf')
s_print_lock = Lock()
start_time = 0

# ------------------------------------------------------------------------ #
# ---------------------------- RUN PARAMETERS ---------------------------- #
# ------------------------------------------------------------------------ #

message_count = 100
are_step_prints_removed = True

# ------------------------------------------------------------------------ #
# ------------------------------------------------------------------------ #
# ------------------------------------------------------------------------ #


# The following are the common default events for all components.
class EventTypes(Enum):
    INIT = "init"
    MFRB = "msgfrombottom"
    MFRT = "msgfromtop"
    MFRP = "msgfrompeer"


class MessageDestinationIdentifiers(Enum):
    LINKLAYERBROADCAST = -1,  # sinngle-hop broadcast, means all directly connected nodes
    NETWORKLAYERBROADCAST = -2  # For flooding over multiple-hops means all connected nodes to me over one or more links

class MessageTypes(Enum):
    PK = "publickey"
    EM = "encryptedmessage"


# A Dictionary that holds a list for the same key
class ConnectorList(dict):

    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(ConnectorList, self).__setitem__(key, [])
        self[key].append(value)


class ConnectorTypes(Enum):
    DOWN = "DOWN"
    UP = "UP"
    PEER = "PEER"


def auto_str(cls):

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        ) + '--------------'

    cls.__str__ = __str__
    return cls


@auto_str
class GenericMessagePayload:

    def __init__(self, messagepayload):
        self.messagepayload = messagepayload

    def getMessagePayload(self):
        return self.messagepayload

    # def __str__(self):
    #     return self.messagepayload



@auto_str
class GenericMessageHeader:

    def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
        self.messagetype = messagetype
        self.messagefrom = messagefrom
        self.messageto = messageto
        self.nexthop = nexthop
        self.interfaceid = interfaceid
        self.sequencenumber = sequencenumber

    def getMessageType(self):
        return self.messagetype

    def getMessageFrom(self):
        return self.messagefrom


@auto_str
class GenericMessage:

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload
        self.uniqueid = str(header.messagefrom) + "-" + str(header.sequencenumber)

    def getHeader(self):
        return self.header

    def getPayload(self):
        return self.payload

    # def __str__(self):
    #     return self.payload


@auto_str
class Event:
    curr_event_id = 0

    def __init__(self, eventsource, event, eventcontent, fromchannel=None,
                 eventid=-1):
        self.eventsource = eventsource
        self.event = event
        self.time = datetime.datetime.now()
        self.eventcontent = eventcontent
        self.fromchannel = fromchannel
        self.eventid = eventid
        if self.eventid == -1:
            self.eventid = self.curr_event_id
            self.curr_event_id += 1

    def __eq__(self, other) -> bool:
        if type(other) is not Event:
            return False

        return self.eventid == other.eventid

    def __hash__(self) -> int:
        return self.eventid


def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


@singleton
class ComponentRegistry:
    components = {}

    def get_component_by_instance(self, instance):
        list_of_keys = list()
        list_of_items = self.components.items()
        for item in list_of_items:
            if item[1] == instance:
                list_of_keys.append(item[0])
        return list_of_keys

    def add_component(self, component):
        key = component.componentname + str(component.componentinstancenumber)
        self.components[key] = component

    def get_component_by_key(self, componentname, componentinstancenumber):
        key = componentname + str(componentinstancenumber)
        return self.components[key]

    def init(self):
        for itemkey in self.components:
            cmp = self.components[itemkey]
            with s_print_lock:
                print("Initializing, ", cmp.componentname, ":", cmp.componentinstancenumber)
            cmp.inputqueue.put_nowait(Event(self, EventTypes.INIT, None))

    def print_components(self):
        for itemkey in self.components:
            cmp = self.components[itemkey]
            with s_print_lock:
                print(f"I am {cmp.componentname}.{cmp.componentinstancenumber}")
            for i in cmp.connectors:
                connectedcmp = cmp.connectors[i]
                for p in connectedcmp:
                    with s_print_lock:
                        print(f"\t{i} {p.componentname}.{p.componentinstancenumber}")

    def get_non_channel_components(self):
        res = []
        for itemkey in self.components:
            cmp = self.components[itemkey]
            if cmp.componentname.find("Channel") != -1:
                continue
            res.append(cmp)
        return res


registry = ComponentRegistry()


class ComponentModel:
    terminated = False

    def on_init(self, eventobj: Event):

        # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_bottom(self, eventobj: Event):

        with s_print_lock:
            print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        with s_print_lock:
            print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_peer(self, eventobj: Event):
        with s_print_lock:
            print(f"{EventTypes.MFRP}  {self.componentname}.{self.componentinstancenumber}")

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

        self.registry = ComponentRegistry()
        self.registry.add_component(self)

        for i in range(self.num_worker_threads):
            t = Thread(target=self.queue_handler, args=[self.inputqueue])
            t.daemon = True
            t.start()

    def connect_me_to_component(self, name, component):
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def connect_me_to_channel(self, name, channel):
        try:
            self.connectors[name] = channel
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = channel
        connectornameforchannel = self.componentname + str(self.componentinstancenumber)
        channel.connect_me_to_component(connectornameforchannel, self)
        self.on_connected_to_channel(name, channel)

    def on_connected_to_channel(self, name, channel):
        with s_print_lock:
            print(f"Connected to channel: {name}:{channel.componentinstancenumber}")

    def on_pre_event(self, event):
        pass

    def unique_name(self):
        return f"{self.componentname}.{self.componentinstancenumber}"

    def terminate(self):
        self.terminated = True

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

    def send_self(self, event: Event):
        self.trigger_event(event)

    # noinspection PyArgumentList
    def queue_handler(self, myqueue):
        while not self.terminated:
            workitem = myqueue.get()

            if workitem.event in self.eventhandlers:
                self.on_pre_event(workitem)
                self.eventhandlers[workitem.event](eventobj=workitem)  # call the handler
            else:
                with s_print_lock:
                    print(f"Event Handler: {workitem.event} is not implemented")
            myqueue.task_done()

    def trigger_event(self, eventobj: Event):
        self.inputqueue.put_nowait(eventobj)


@singleton
class Topology:
    nodes = {}
    channels = {}


    def construct_sender_receiver(self, sendertype, receivertype, channeltype):
        self.sender = sendertype(sendertype.__name__, 0)
        self.receiver = receivertype(receivertype.__name__, 1)
        ch = channeltype(channeltype.__name__, "0-1")
        self.G = nx.Graph()
        self.G.add_nodes_from([0, 1])
        self.G.add_edges_from([(0, 1)])
        self.nodes[self.sender.componentinstancenumber] = self.sender
        self.nodes[self.receiver.componentinstancenumber] = self.receiver
        self.channels[ch.componentinstancenumber] = ch
        self.sender.connect_me_to_channel(ConnectorTypes.DOWN, ch)
        self.receiver.connect_me_to_channel(ConnectorTypes.DOWN, ch)


    def start(self):
        N = len(self.G.nodes)
        self.lock = Lock()
        ComponentRegistry().init()


    # Returns the list of neighbors of a node
    def get_neighbors(self, nodeId):
        return sorted([neighbor for neighbor in self.G.neighbors(nodeId)])

    def get_predecessors(self, nodeId):
        return sorted([neighbor for neighbor in self.G.predecessors(nodeId)])

    def get_successors(self, nodeId):
        return sorted([neighbor for neighbor in self.G.neighbors(nodeId)])

    # Returns the list of neighbors of a node
    def get_neighbor_count(self, nodeId):
        # return len([neighbor for neighbor in self.G.neighbors(nodeId)])
        return self.G.degree[nodeId]


class Node(ComponentModel):

    def distribute_key(self, messageTo):

        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        gmh = GenericMessageHeader(MessageTypes.PK,self.componentinstancenumber,messageTo)
        gmp = GenericMessagePayload(pem)
        gm = GenericMessage(gmh,gmp)

        with s_print_lock:
            print(f"I am {self.componentname}.{self.componentinstancenumber} \
            sending public key to: \"{messageTo}\"")

        evt = Event(self, EventTypes.MFRT, gm)
        self.send_down(evt)


    def begin_messaging(self, msg):

        global are_step_prints_removed

        msg_encrypted = self.destination_public_key.encrypt(msg, \
                                           padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), \
                                                        algorithm=hashes.SHA256(),label=None))

        if self.componentinstancenumber == 0:
            gmh = GenericMessageHeader(MessageTypes.EM,0,1)
        else:
            gmh = GenericMessageHeader(MessageTypes.EM,1,0)
        gmp = GenericMessagePayload(msg_encrypted)
        gm = GenericMessage(gmh,gmp)

        if not are_step_prints_removed:
            with s_print_lock:
                print(f"I am {self.componentname}.{self.componentinstancenumber} \
                sending encrypted message with content: \"{msg}\"")

        evt = Event(self, EventTypes.MFRT, gm)
        self.send_down(evt)



    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):

        global are_step_prints_removed, start_time

        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

        if eventobj.eventcontent.getHeader().getMessageType() == MessageTypes.PK:

            self.destination_public_key = load_pem_public_key(eventobj.eventcontent.getPayload().getMessagePayload())

            with s_print_lock:
                print(f"I am {self.componentname}.{self.componentinstancenumber} \
                just received public key from {eventobj.eventcontent.getHeader().getMessageFrom()}")

            msg = b"A message from Sender Node Alice to Channel"

            start_time = time.time()

            for i in range(0, message_count):

                if not are_step_prints_removed:
                    with s_print_lock:
                        print(f"I am {self.componentname}.{self.componentinstancenumber} starting message {i} with content: \"{msg}\"")

                self.begin_messaging(msg)


        else:
            msg_decrypted = self.private_key.decrypt(eventobj.eventcontent.getPayload().getMessagePayload(), \
                                                padding.OAEP( mgf=padding.MGF1(algorithm=hashes.SHA256()), \
                                                              algorithm=hashes.SHA256(),label=None))

            if not are_step_prints_removed:
                with s_print_lock:
                    print(f"I am {self.componentname}.{self.componentinstancenumber} \
                     just received encryted message with content: \"{msg_decrypted}\"")

            self.receive_counter += 1

            if self.receive_counter == message_count:
                with s_print_lock:
                    print(f"{message_count} message(s) are sent in {time.time() - start_time} seconds.")



    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)
        self.private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.public_key = self.private_key.public_key()

        self.receive_counter = 0

    def on_init(self, eventobj: Event):

        if self.componentinstancenumber == 1: # Bob

            self.distribute_key(0)



class ChannelEventTypes(Enum):
    INCH = "processinchannel"
    DLVR = "delivertocomponent"


class Channel(ComponentModel):

    def on_init(self, eventobj: Event):

        pass

    # Overwrite onSendToChannel if you want to do something in the first pipeline stage
    def on_message_from_top(self, eventobj: Event):
        # channel receives the input message and will process the message by the process event in the next pipeline stage
        # Preserve the event id through the pipeline
        myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH,
                        eventobj.eventcontent, eventid=eventobj.eventid)
        self.channelqueue.put_nowait(myevent)

    # Overwrite onProcessInChannel if you want to do something in interim pipeline stage
    def on_process_in_channel(self, eventobj: Event):
        # Add delay, drop, change order whatever....
        # Finally put the message in outputqueue with event deliver
        # Preserve the event id through the pipeline
        myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR,
                        eventobj.eventcontent, eventid=eventobj.eventid)
        self.outputqueue.put_nowait(myevent)

    # Overwrite onDeliverToComponent if you want to do something in the last pipeline stage
    # onDeliver will deliver the message from the channel to the receiver component using messagefromchannel event
    def on_deliver_to_component(self, eventobj: Event):
        callername = eventobj.eventsource.componentinstancenumber
        for item in self.connectors:
            callees = self.connectors[item]
            for callee in callees:
                calleename = callee.componentinstancenumber
                # print(f"I am connected to {calleename}. Will check if I have to distribute it to {item}")
                if calleename == callername:
                    pass
                else:
                    # Preserve the event id through the pipeline
                    myevent = Event(eventobj.eventsource, EventTypes.MFRB,
                                    eventobj.eventcontent, self.componentinstancenumber,
                                    eventid=eventobj.eventid)
                    callee.trigger_event(myevent)

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.outputqueue = queue.Queue()
        self.channelqueue = queue.Queue()
        self.eventhandlers[ChannelEventTypes.INCH] = self.on_process_in_channel
        self.eventhandlers[ChannelEventTypes.DLVR] = self.on_deliver_to_component

        for i in range(self.num_worker_threads):
            # note that the input queue is handled by the super class...
            t = Thread(target=self.queue_handler, args=[self.channelqueue])
            t1 = Thread(target=self.queue_handler, args=[self.outputqueue])
            t.daemon = True
            t1.daemon = True
            t.start()
            t1.start()



def Main():
    topo = Topology()
    # topo.construct_single_node(Node, 0)
    topo.construct_sender_receiver(Node, Node, Channel)
    topo.start()
    while (True): pass

if __name__ == "__main__":
    Main()