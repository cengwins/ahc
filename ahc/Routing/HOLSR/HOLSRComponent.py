import time
import traceback

from ahc.Ahc import ComponentModel, Event, GenericMessage, Lock, \
    GenericMessageHeader, GenericMessagePayload, Topology, EventTypes
from enum import Enum
from datetime import datetime
import uuid

from ahc.Routing.HOLSR.mpr import obtain_mpr
from ahc.Routing.HOLSR.utils import RepeatDeltaTimer, Tracing, keys_to_set


class HOLSRMessageTypes(Enum):
    DATA = "holsr.data"
    HELLO = "holsr.hello"
    TC = "holsr.tc"
    HTC = "holsr.htc"
    CIA = "holsr.cia"


class OLSRLinkStatus(Enum):
    Unidirectional = "uni"
    Bidirectional = "bi"


class OLSRMessageHeader(GenericMessageHeader):
    pass


class OLSRMessagePayload(GenericMessagePayload):
    pass


class OLSRComponent(ComponentModel):
    def __init__(self, component_name, component_id, context=None,
                 configurationparameters=None, num_worker_threads=1):
        super().__init__(component_name, component_id, context=context,
                         configurationparameters=configurationparameters,
                         num_worker_threads=num_worker_threads)
        self.lock = Lock()
        # create an address for the node
        self.address = str(uuid.uuid4())
        # for debugging
        Tracing().register_node(self.address, component_id)
        # handlers for each message kind
        self.message_handlers = {
            HOLSRMessageTypes.DATA: lambda p: self.on_data_handler(p),
            HOLSRMessageTypes.HELLO: lambda p: self.on_hello_handler(p),
            HOLSRMessageTypes.TC: lambda p: self.on_tc_handler(p),
        }
        # list of neighbors to which there
        # exists a valid bidirectional link
        self.valid_bidirectional_links = {}
        # the list of neighbors are heard by this node,
        # but a bidirectional link is not yet validated
        self.non_validated_neighbors = set()
        # neighbor table
        self.neighbor_table = {}
        # mpr set
        self.mpr_set = set()
        self.mpr_sequence_number = 0
        # ms set
        self.ms_set = set()
        self.ms_sequence_number = 0
        # sequence number cache for tc messages
        self.tc_seq_cache = {}
        # routing table
        self.routing_table = {}
        # topology table
        self.topology_table = {}
        # start the component timer
        current_time = datetime.now()
        self.last_hello = current_time
        self.last_tc = current_time
        RepeatDeltaTimer().register_function(self.on_time)

    def on_time(self, current_time, _delta):
        if (current_time - self.last_hello).total_seconds() > 0.25:
            self.last_hello = current_time
            self.broadcast_hello()
        if (current_time - self.last_tc).total_seconds() > 0.5:
            self.last_tc = current_time
            self.broadcast_tc()

    def broadcast_hello(self):
        payload = {'address': self.address}
        self.lock.acquire()
        try:
            payload['mpr_set'] = {a for a in self.mpr_set}
            payload['valid_links'] = keys_to_set(self.valid_bidirectional_links)
            payload['non_validated'] = [a for a in self.non_validated_neighbors]

        finally:
            self.lock.release()
        self.broadcast_msg(HOLSRMessageTypes.HELLO, OLSRMessagePayload(payload))

    def broadcast_tc(self):
        payload = {'address': self.address, 'origin': self.address}
        self.lock.acquire()
        try:
            payload['ms_set'] = {a for a in self.ms_set}
            payload['ms_seq_num'] = self.ms_sequence_number
        finally:
            self.lock.release()
        self.broadcast_msg(HOLSRMessageTypes.TC, OLSRMessagePayload(payload))

    def broadcast_msg(self, msg_type, payload):
        msg_from = self.componentname + "-" + str(self.componentinstancenumber)
        for target in Topology().get_neighbors(self.componentinstancenumber):
            hdr = OLSRMessageHeader(msg_type, msg_from, self.componentname + "-" + str(target),
                                    interfaceid=str(self.componentinstancenumber) + "-" + str(target))
            self.send_down(Event(self, EventTypes.MFRT, GenericMessage(hdr, payload)))

    def on_message_from_bottom(self, eventobj: Event):
        hdr = eventobj.eventcontent.header
        # we expect both from and to fields to
        # start with this component's name
        if hdr.messagefrom.split("-")[0] != self.componentname:
            return
        if hdr.messageto.split("-")[0] != self.componentname:
            return
        payload = eventobj.eventcontent.payload.messagepayload
        # dispatch to the expected message handler
        if hdr.messagetype in self.message_handlers:
            self.lock.acquire()
            try:
                self.message_handlers[hdr.messagetype](payload)
            except Exception as e:
                print(f"ERROR: cannot handle msg of type {hdr.messagetype}: {e}\n")
                traceback.print_exc()
            finally:
                self.lock.release()

    def on_hello_handler(self, payload):
        self.on_hello(payload['address'], payload['valid_links'],
                      payload['non_validated'], payload['mpr_set'])

    def on_hello(self, sender_address, valid_links, non_validated, sender_mpr):
        self.update_links(sender_address, valid_links, non_validated)
        self.select_mpr()
        self.update_ms(sender_address, sender_mpr)
        self.calculate_route_table()
        # for debugging
        if self.componentinstancenumber == 0:
            Tracing().update_edges(list(self.topology_table.keys()))

    def update_links(self, sender_address, valid_links, non_validated):
        # if the sender has us in the non-validated list;
        # then we have already sent them a HELLO message.
        # which means the connection is bidirectionally validated.
        # similarly, if our address is already in the sender's
        # valid links list; update the two-hop list with the new list.
        if self.address in non_validated or self.address in valid_links:
            # promote sender_address from non-validated to bidirectional links
            if sender_address in self.non_validated_neighbors:
                self.non_validated_neighbors.discard(sender_address)
            self.valid_bidirectional_links[sender_address] = valid_links
            # update information in the neighbor table as well
            self.neighbor_table[sender_address] = {
                'status': OLSRLinkStatus.Bidirectional,
                'two_hop': valid_links}
        # the alternative is that the bidirectional
        # verification is not (yet) completed. add the sender
        # to the non-validated neighbors list.
        else:
            # demote from bidirectional links if exists
            if sender_address in self.valid_bidirectional_links:
                self.valid_bidirectional_links.pop(sender_address)
            self.non_validated_neighbors.add(sender_address)
            # update information in the neighbor table as well
            self.neighbor_table[sender_address] = {
                'status': OLSRLinkStatus.Unidirectional,
                'two_hop': valid_links}

    def select_mpr(self):
        prev_mpr_set = self.mpr_set
        self.mpr_set = obtain_mpr(self.valid_bidirectional_links)
        if prev_mpr_set == self.mpr_set:
            self.mpr_sequence_number += 1

    def update_ms(self, sender_address, sender_mpr):
        # if we are in the sender's MPR set,
        # add the neighbor's address to the MS
        # set and increase the sequence number.
        if self.address in sender_mpr:
            if sender_address not in self.ms_set:
                self.ms_set.add(sender_address)
                self.ms_sequence_number += 1
        # if not; but we used to be there; then
        # the neighbor node discarded us as an MPR.
        # remove the neighbor from the MS set
        # and increase the sequence number
        elif sender_address in self.ms_set:
            self.ms_set.discard(sender_address)
            self.ms_sequence_number += 1

    def on_tc_handler(self, payload):
        self.on_tc(payload['address'], payload['origin'],
                   payload['ms_set'], payload['ms_seq_num'])

    # sender_address is the message originator.
    # last_hop is the node that passed us the tc message.
    def on_tc(self, last_hop, sender_address, sender_ms, sender_ms_sequence_number):
        # discard our own TC messages
        if sender_address == self.address:
            return

        # discard tc messages with an old sequence number
        if sender_address in self.tc_seq_cache:
            if self.tc_seq_cache[sender_address] >= sender_ms_sequence_number:
                return
        self.tc_seq_cache[sender_address] = sender_ms_sequence_number

        # we are looking for entries whose destination is the sender of the TC message
        for (_, destination), (sequence_number, _) in self.topology_table.items():
            # if the MS sequence number is already higher;
            # we can discard the message and return
            if destination == sender_address and sequence_number > sender_ms_sequence_number:
                return

        # otherwise, we remove each entry for the sender
        # address as destination, to add them later
        keys_to_pop = []
        for k in self.topology_table.keys():
            (destination, _) = k
            if destination == sender_address:
                keys_to_pop.append(k)
        for k in keys_to_pop:
            self.topology_table.pop(k)

        # insert the new topology data to the table
        current_time = datetime.now()
        for dst in sender_ms:
            self.topology_table[(dst, sender_address)] = (sender_ms_sequence_number, current_time)

        # update the routing table
        self.calculate_route_table()

        # if this node is an MPR of the last hop; forward the message
        if last_hop in self.ms_set:
            self.broadcast_msg(HOLSRMessageTypes.TC, OLSRMessagePayload({
                'address': self.address, 'origin': sender_address,
                'ms_set': sender_ms, 'ms_seq_num': sender_ms_sequence_number}))

    def calculate_route_table(self):
        # start populating a new routing table by
        # adding one-hop neighbors to hop distance 1
        routes = {}
        for one_hop in self.valid_bidirectional_links.keys():
            routes[one_hop] = (one_hop, 1)
        # we will iterate the topology table keys (which are node pairs)
        # to add routes at hop_distance away at each iteration.
        # once no changes occur; we break the loop.
        hop_distance = 0
        loop = True
        while loop:
            loop = False
            hop_distance += 1
            for (destination, last_hop) in self.topology_table.keys():
                if destination != self.address and destination not in routes:
                    if last_hop in routes:
                        (next_hop, distance) = routes.get(last_hop)
                        if distance == hop_distance:
                            routes[destination] = (next_hop, distance + 1)
                            loop = True
        self.routing_table = routes

    def get_route(self, destination):
        if destination not in self.routing_table:
            return None
        (next_hop, _) = self.routing_table.get(destination)
        return next_hop

    def send_data_to(self, sender, destination, data):
        # if the routing is not yet complete;
        # drop the message.
        next_hop = self.get_route(destination)
        if next_hop is not None:
            self.broadcast_msg(HOLSRMessageTypes.DATA, OLSRMessagePayload({
                'address': sender, 'destination': destination,
                'next_hop': next_hop, 'data': data}))

    def on_data_handler(self, payload):
        self.on_data_fwd(payload['address'], payload['destination'],
                         payload['next_hop'], payload['data'])

    def on_data_fwd(self, sender, destination, me, data):
        # drop messages not forwarded to us. normally,
        # if we did p2p we wouldn't need this step.
        # but to avoid our virtual address to node ids;
        # we send these messages to all our neighbors,
        # and then drop it here.
        if me == self.address:
            if destination == self.address:
                # if we're here; the message was directed to us.
                self.on_data(sender, data)
            else:
                # we were indeed the next hop; but not the
                # ultimate destination. keep forwarding the
                # mail using the routing table.
                self.send_data_to(sender, destination, data)

    def on_data(self, sender, data):
        # TODO
        pass


class HOLSRComponent(OLSRComponent):
    def __init__(self, component_name, component_id, context=None,
                 configurationparameters=None, num_worker_threads=1):
        super().__init__(component_name, component_id, context=context,
                         configurationparameters=configurationparameters,
                         num_worker_threads=num_worker_threads)
        layers_set = {0}
        if configurationparameters is not None:
            if configurationparameters['layers'] is not None:
                layers_set = configurationparameters['layers']
        is_head = len(layers_set) > 1
        self.layers = layers_set
        self.cluster_head = self.address if is_head else ''
        self.cluster_dist = 0
        self.last_cia = datetime.now()
        # members of the cluster (for cluster heads)
        self.cluster_member_table = {}
        # decorate old message handlers to discard messages from different clusters,
        # add HOLSR-specific message handlers,
        # then decorate both old and new handlers to discard messages from different layers
        self.message_handlers[HOLSRMessageTypes.CIA] = lambda p: self.on_cia_handler(p)
        self.message_handlers[HOLSRMessageTypes.HTC] = lambda p: self.on_htc_handler(p)

    def on_hello_handler(self, payload):
        if len(self.layers.intersection(payload['layers'])) > 0:
            if payload['cluster_head'] == self.cluster_head:
                super().on_hello_handler(payload)

    def on_tc_handler(self, payload):
        if len(self.layers.intersection(payload['layers'])) > 0:
            if payload['cluster_head'] == self.cluster_head:
                super().on_tc_handler(payload)

    def on_time(self, current_time, delta):
        super().on_time(current_time, delta)
        if (current_time - self.last_cia).total_seconds() > 0.25:
            self.last_cia = current_time
            self.broadcast_cia()

    def broadcast_msg(self, msg_type, payload):
        # decorate all outgoing messages with cluster and layer info
        if 'layers' not in payload.messagepayload:
            payload.messagepayload['layers'] = self.layers
        if 'cluster_head' not in payload.messagepayload:
            payload.messagepayload['cluster_head'] = self.cluster_head
        super().broadcast_msg(msg_type, payload)

    def broadcast_cia(self):
        # only cluster heads broadcast initial CIA messages. others relay
        if self.cluster_head == self.address:
            self.broadcast_msg(HOLSRMessageTypes.CIA, OLSRMessagePayload({
                'address': self.address, 'cluster_head': self.address, 'distance': 0}))

    def on_cia_handler(self, payload):
        self.on_cia(payload['address'], payload['layers'],
                    payload['cluster_head'], payload['distance'])

    def on_cia(self, sender_address, layers, sender_head, sender_distance):
        # discard our own CIA messages
        if self.address == sender_head:
            return
        # CIA msgs of lower levels or this level contribute to the cluster member table
        if self.cluster_head == self.address:
            if self.is_from_lower_levels(layers):
                inserted = False
                if sender_head not in self.cluster_member_table:
                    self.cluster_member_table[sender_head] = []
                else:
                    for i in range(len(self.cluster_member_table[sender_head])):
                        (member_addr, member_hop) = self.cluster_member_table[sender_head][i]
                        if member_addr == sender_address:
                            self.cluster_member_table[sender_head][i] = (sender_address, sender_distance)
                            inserted = True
                            break
                if not inserted:
                    self.cluster_member_table[sender_head].append((sender_address, sender_distance))
        # for cluster selection; don't consider messages from other layers
        if len(self.layers.intersection(layers)) == 0:
            return
        # our distance is one hop more than the sender's
        distance = sender_distance + 1
        # if the first CIA msg, or a closer cluster head is seen
        if self.cluster_head == '' or distance < self.cluster_dist:
            # update the cluster head and distance
            self.cluster_head = sender_head
            self.cluster_dist = distance
            # propagate the message
            self.broadcast_msg(HOLSRMessageTypes.CIA, OLSRMessagePayload({
                'address': self.address, 'cluster_head': sender_head, 'distance': distance}))

    def is_from_lower_levels(self, sender_layers):
        for self_layer in self.layers:
            for sender_layer in sender_layers:
                if sender_layer <= self_layer:
                    return True
        return False

    def on_htc_handler(self, payload):
        self.on_htc(payload['layers'], payload['address'], payload['members'])

    def on_htc(self, _layers, cluster_head, cluster_member_list):
        # Only cluster heads maintain a member table
        if self.cluster_head == self.address:
            self.cluster_member_table[cluster_head] = cluster_member_list

    def broadcast_htc(self):
        # only cluster heads broadcast HTC messages
        if self.cluster_head == self.address:
            payload = {'address': self.address, 'members': []}
            self.lock.acquire()
            try:
                if self.address in self.cluster_member_table:
                    payload['members'] = [a for a in self.cluster_member_table[self.address]]
            finally:
                self.lock.release()
            self.broadcast_msg(HOLSRMessageTypes.HTC, OLSRMessagePayload(payload))


