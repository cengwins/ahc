import time

from ahc.Ahc import ComponentModel, Event, GenericMessage, MessageDestinationIdentifiers, GenericMessageHeader, EventTypes, \
    ComponentRegistry, Lock, \
    Thread, Topology
from enum import Enum
import datetime
import random


class CGSREventTypes(Enum):
    HELLO = "HELLO_MESSAGE"
    RREQ = 'ROUTE_REQUEST_PACKET'
    RREP = 'RREP'


class CGSRMessageType(Enum):
    HELLO = "HELLO_MESSAGE"
    RREQ = 'ROUTE_REQUEST_PACKET'
    RREP = 'RREP'
    GENERATE_HELLO = "GENERATE_HELLO"
    GENERATE_RREQ = "GENERATE_RREQ"


class CGSRRouter(ComponentModel):

    def __init__(self, componentname, componentid):
        super(CGSRRouter, self).__init__(componentname, componentid)
        # self.eventhandlers[CGSREventTypes.HELLO] = self.onHello
        self.eventhandlers[CGSREventTypes.RREQ] = self.onRREQ
        self.eventhandlers[CGSREventTypes.RREP] = self.onRREP
        self.neighbor_table = []  # hello mesajinin icinde
        # {'neighbor_id','neighbor_role'}
        self.cluster_adjacency_table = []
        # {neighbor_cluster_head_id,gateway_node_id[]}
        self.two_hop_topology_database = []
        self.message_id_table = []
        self.cluster_addres_list = []
        self.prev_RREQs = []
        self.message_id = 0
        self.sleep = random.randint(1, 5)
        self.node_status = 'C_UNDECIDED'
        self.neighbors = Topology().get_neighbors(self.componentinstancenumber)
        # print('__init__')
        self.send_self(Event(self, EventTypes.INIT, None))

    def on_init(self, eventobj: Event):
        super(CGSRRouter, self).on_init(eventobj)

        self.onNeighbors()
        # self.generateHello()

    def on_message_from_peer(self, eventobj: Event):

        payload = eventobj.eventcontent
        if payload == CGSRMessageType.GENERATE_HELLO:
            sender_status = self.node_status
            neighbor_table = self.neighbor_table
            cat_extension = [] if self.node_status == 'C_MEMBER' else None
            if self.node_status == 'C_MEMBER':
                for item in self.cluster_adjacency_table:
                    cat_extension.append(item['neighbor_cluster_head_id'])
            payload = {'sender_status': sender_status, 'neighbor_table': neighbor_table,
                       'cluster_extension': cat_extension}

            for node in self.neighbors:
                header = GenericMessageHeader(CGSRMessageType.HELLO,
                                              CGSRRouter.__name__ + "-" + str(self.componentinstancenumber),
                                              CGSRRouter.__name__ + "-" + str(node),
                                              interfaceid=str(self.componentinstancenumber) + "-" + str(node))
                eventContent = GenericMessage(header, payload)
                self.send_down(Event(self, EventTypes.MFRT, eventContent))
        if payload == CGSRMessageType.GENERATE_RREQ:
            # print('generate rreq')
            node = Topology().get_random_node()
            payload = {'message_id': self.message_id,
                       'target_address': CGSRRouter.__name__ + "-" + str(node.componentinstancenumber),
                       'num1': len(self.cluster_adjacency_table), 'num2': len(self.cluster_addres_list),
                       'pair_list': self.cluster_adjacency_table
                , 'cluster_list': self.cluster_addres_list,'calculated_route':[CGSRRouter.__name__ + "-" + str(node.componentinstancenumber)],
                       'cluster_addresses':[]}
            header=GenericMessageHeader(CGSRMessageType.RREQ,
                                              CGSRRouter.__name__ + "-" + str(self.componentinstancenumber),
                                              CGSRRouter.__name__ + "-" + str(self.neighbors[0]),
                                              interfaceid=str(self.componentinstancenumber) + "-" + str(self.neighbors[0]))
            eventContent = GenericMessage(header, payload)
            self.send_down(Event(self, EventTypes.MFRT, eventContent))

    def onNeighbors(self):
        # print(self.componentinstancenumber)
        # print(self.neighbors)

        if self.neighbors and self.componentinstancenumber <= self.neighbors[0]:
            self.node_status = "C_HEAD"
        else:
            self.node_status = 'C_MEMBER'
        # print(f"node status for {self.unique_name()}:  " + self.node_status)
        # for node in self.neighbors:
        #     if node>self.neighbors[0]: self.neighbor_table.append({'neighbor_id':node,'neighbor_role':'C_MEMBER'})
        #     else: self.neighbor_table.append({'neighbor_id':node,'neighbor_role':'C_HEAD'})
        # for item in self.neighbor_table:
        #     print(item)

    def on_message_from_bottom(self, eventobj: Event):
        # print('router on message from bottom')
        message_destination = eventobj.eventcontent.header.messageto.split("-")[0]

        # print(f"{self.componentinstancenumber} received {message_destination}")
        if message_destination == CGSRRouter.__name__:  # process only the messages targeted to this component...
            message_source_id = eventobj.eventcontent.header.messagefrom.split("-")[1]
            message_type = eventobj.eventcontent.header.messagetype
            content = eventobj.eventcontent.payload
            print(message_type)
            if message_type == CGSRMessageType.HELLO:
                self.onHello(eventobj)
            if message_type==CGSRMessageType.RREQ:
                # print('rreq geldi')
                self.onRREQ(eventobj)


    def update_cat(self, header, payload):
        sender_id = header.messagefrom
        neighbor_table = payload['neighbor_table']
        summarized_cat = payload['cluster_extension']
        if self.node_status == "C_MEMBER":
            for index, item in enumerate(neighbor_table):
                if item['neighbor_role'] == 'C_HEAD' and item['neighbor_id'] != self.neighbors[0]:
                    self.cluster_adjacency_table.append({'neighbor_cluster_head_id': item['neighbor_id'],
                                                         'gateway_node_id': sender_id})

        if self.node_status == "C_HEAD":
            if any(item.get('neighbor_role') == 'C_HEAD' for item in neighbor_table):
                index = next(i for i, item in enumerate(neighbor_table) if
                             item["neighbor_role"] == 'C_HEAD')
                self.cluster_adjacency_table.append({'neighbor_cluster_head_id': neighbor_table[index]['neighbor_id'],
                                                     'gateway_node_id': sender_id})
            if summarized_cat is not None:
                for entry in summarized_cat:
                    if not any(item.get('neighbor_cluster_head_id') == entry for item in self.cluster_adjacency_table):
                        self.cluster_adjacency_table.append(
                            {'neighbor_cluster_head_id': entry, 'gateway_node_id': sender_id})

    def update_two_hop_topology_database(self, payload):
        neighbor_table = payload['neighbor_table']

        for item in neighbor_table:
            if not any(element.get('neighbor_id') == item['neighbor_id'] for element in self.neighbor_table):
                self.two_hop_topology_database.append(item['neighbor_id'])

    def onHello(self, eventobj: Event):
        # time.sleep(1)
        # print(f"neighbor table for {self.unique_name()}:  ")
        # print(self.neighbor_table)

        message = eventobj.eventcontent
        message_header = message.header
        message_payload = message.payload

        self.update_cat(message_header, message_payload)
        self.update_two_hop_topology_database(message_payload)
        if not any(item.get('neighbor_id') == message_header.messagefrom for item in self.neighbor_table):

            self.neighbor_table.append(
                {'neighbor_id': message_header.messagefrom, 'neighbor_role': message_payload['sender_status']})
        else:
            pass

    def onRREQ(self, eventobj: Event):
        message = eventobj.eventcontent
        message_header = message.header
        message_payload = message.payload
        if message_payload['target_address']==CGSRRouter.__name__+'-'+str(self.componentinstancenumber):
            message.payload['calculated_route'].append(CGSRRouter.__name__+'-'+str(self.componentinstancenumber))
            self.send_self(Event(self,CGSREventTypes.RREP,message))
            return
        self.prev_RREQs.append(message)
        if self.node_status == "C_MEMBER":
            if any(neighbor.get('neighbor_id') == message_payload['target_address'] for neighbor in self.neighbor_table):

                message.header.messageto=message_payload['target_address']
                self.send_down(Event(self, EventTypes.MFRT, message))
            else:
                if any(item.get('gateway_node_address') == CGSRRouter.__name__+'-'+str(self.componentinstancenumber) for item in
                       message_payload['pair_list']):
                    message_header.messageto = self.neighbors[0]
                    msg = GenericMessage(message_header, message_payload)
                    self.send_down(Event(self, CGSRMessageType.RREQ, msg))
                else:
                    return
        elif self.node_status == "C_HEAD":
            if message_payload['message_id'] in self.message_id_table:
                return
            else:
                message_payload['cluster_list'].append(CGSRRouter.__name__+'-'+str(self.componentinstancenumber))
            if any(neighbor.get('neighbor_id') == message_payload['target_address'] for neighbor in
                   self.neighbor_table) or message_payload['target_address'] in self.two_hop_topology_database:
                message.header.messageto = message_payload['target_address']
                self.send_down(Event(self, EventTypes.MFRT, message))
                # uni-cast RREQ to D

            else:
                arr = []
                for item in self.cluster_adjacency_table:
                    arr.append(item['neighbor_cluster_head_id'])
                for index, CH in enumerate(arr):
                    if CH in self.prev_RREQs:
                        continue
                    elif CH in message_payload['cluster_list']:
                        continue
                    else:
                        message_payload['pair_list'].append(
                            {self.prev_RREQs[index]['gateway_node'], self.prev_RREQs[index]['adj_cls_id']})


    def onRREP(self, eventobj: Event):
        message = eventobj.eventcontent
        message_header = message.header
        message_payload = message.payload
        sent_message_payload={}
        sent_message_header={}
        print('onRREP')
        sent_to_x = False
        if self.node_status == 'C_HEAD':
            sent_message_payload['num1']= message_payload['num1'] - 1
            # cluster address[num1]in gateway nodeunu bulacagiz, mesaji node'a forwardla
            cluster_head_id = message_payload[message_payload['num1']]
            calculated_route = message_payload['calculated_route'][message_payload['num2']]
            if any(item.get('neighbor_cluster_head_id') == cluster_head_id for item in self.cluster_adjacency_table):
                index = next(i for i, item in enumerate(self.cluster_adjacency_table) if
                             item["neighbor_cluster_head_id"] == cluster_head_id)
                for gateway_node in self.cluster_adjacency_table[index]['gateway_node_id']:
                    if any(item.get('2hop') == calculated_route and item.get('neighbor') == gateway_node for
                           item in self.two_hop_topology_database):
                        sent_to_x = True
                        message_header.messageto = "CGSRouter"+'-'+gateway_node
                        msg = GenericMessage(message_header, message_payload)
                        self.send_down(Event(self, CGSRMessageType.RREP, msg))

                if not sent_to_x:
                    message_payload['num2'] += 1
                    message_payload['calculated_route'].append(CGSRRouter.__name__+'-'+self.componentinstancenumber)
        elif self.node_status == "C_MEMBER":
            message_payload['num2'] += 1
            message_payload['calculated_route'].append(CGSRRouter.__name__+'-'+self.componentinstancenumber)
            if any(item.get('neighbor_id') == message_payload['cluster_address_list'][message_payload['num1']]
                   for item in self.neighbor_table):
                message_header.messageto = message_payload['cluster_address_list'][
                    message_payload['num1']]
                msg = GenericMessage(message_header, message_payload)
                self.send_down(Event(self, CGSRMessageType.RREP, msg))
            elif any(item.get('neighbor_cluster_head_id') == message_payload['cluster_address_list'][
                message_payload['num1']]
                     for item in self.cluster_adjacency_table):
                index = next(i for i, item in enumerate(self.cluster_adjacency_table) if
                             item["neighbor_cluster_head_id"] == message_payload['cluster_address_list'][
                                 message_payload['num1']])
                message_header.messageto = message_payload['cluster_adjacency_table'][index]
                msg = GenericMessage(message_header, message_payload)
                self.send_down(Event(self, CGSRMessageType.RREP, msg))
                # send rrep to self.cluster_adjacency_table[index]['gateway_node_id']den birine


class HelloMessage(GenericMessage):
    # neighbor_table={'neighbor_id','neighbor_role'}
    # cluster_extension=['adj cluster head address']
    # payload={'sender_status':'member/head','neighbor_table':[],'ClusterAdjacencyExtension':[]}
    def __init__(self, header, payload):
        super(HelloMessage, self).__init__(header, payload)


class ClusterAdjacencyExtension(GenericMessage):
    """
    sadece member nodelar ekler
    helloya extent
    adj. cluster head1 Ip add.
    ....
    """

    def __init__(self, payload):
        super(ClusterAdjacencyExtension, self).__init__(GenericMessageHeader(), payload)


class RouteRequestPacket(GenericMessage):
    """
    ilk RREQ mesaji broadcast
    sadece headlere bu mesaj flood, route discovery
    target address
    message id: unique msg id
    pairlar: arr[num1]: (gateway node, adjacent cluster address(id)-> kendi cluster head id ve CAT'ten diger idleri aliyor)
             arr[num2]: cluster addresses
    headerda destination node adresi: messageto
    """

    payload = {}

    def __init__(self, payload):
        super(RouteRequestPacket, self).__init__(GenericMessageHeader(), payload)


class RREPPacket(GenericMessage):
    """
    msg id, RREQdan gelen idyi buraya kopyala d node yapar
    cluster adres list[num1] ???? sayfa 16
    calculated rute[num2] ???? ch hesapliyor xd
    """

    def __init__(self, payload):
        super(RREPPacket, self).__init__(GenericMessageHeader(), payload)


class SourceRouting(GenericMessage):
    # num,
    # current num,currently visited address,
    # address[num]
    def __init__(self, payload):
        super(SourceRouting, self).__init__(GenericMessageHeader(), payload)
