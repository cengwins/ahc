import time
from enum import Enum
from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes

registry = ComponentRegistry()
topo = Topology()

rerr = 1


class AODV_ABRMessageTypes(Enum):
    RREQ = "RREQ"
    RREP = "RREP"
    RERR = "RERR"
    BRRQ = "BRRQ"
    BRRP = "BRRP"
    OVRH = "OVRH"
    DATA = 'DATA'


# # define your own message header structure
class AODV_ABRMessageHeader(GenericMessageHeader):
    def __init__(self, *args):
        super().__init__(*args[:6])
        self.rreq_id = args[6]
        self.hop_count = args[7]
        self.int_sender = args[8]


# define your own message payload structure
class AODV_ABRMessagePayload(GenericMessagePayload):
    def __init__(self, *args):
        super().__init__(*args[:1])
        self.toNode = args[1]


class AODV_ABRComponent(ComponentModel):

    def __init__(self, componentname, componentinstancenumber):
        print(f"Initializing {componentname}.{componentinstancenumber}")
        super().__init__(componentname, componentinstancenumber)
        neighbour_list = topo.get_neighbors(self.componentinstancenumber)
        self.NeighbourList = neighbour_list
        self.RoutingTable = dict()
        self.AlternateRouteTable = dict()
        self.rreq_list = set()
        self.BBRP_Responses = dict()

    def on_message_from_bottom(self, eventobj: Event):
        msg = eventobj.eventcontent
        hdr = msg.header
        py = msg.payload
        message_source = hdr.messagefrom

        if hdr.messagetype == AODV_ABRMessageTypes.RREQ:
            self.updateRoutingTableNeighbours()

            if hdr.rreq_id in self.rreq_list:
                # print('Ignoring duplicate RREQ message with rreq id ', hdr.rreq_id)
                return
            else:
                self.rreq_list.add(hdr.rreq_id)
                if message_source in self.RoutingTable.keys():  # update the route table if the entries are not fresh
                    route = self.RoutingTable[message_source]
                    if hdr.sequencenumber > int(route['Seq_No']):
                        route['Seq_No'] = hdr.sequencenumber
                    elif hdr.sequencenumber == int(route['Seq_No']) and hdr.hop_count < route['Hop_Count']:
                        route['Hop_Count'] = hdr.hop_count
                        route['Next_Hop'] = message_source
                else:
                    if hdr.messagefrom != self.componentinstancenumber:  # if the source is not in routing table, create an entry
                        self.RoutingTable[message_source] = {'Dest': str(message_source),
                                                            'Next_Hop': str(hdr.int_sender),
                                                            'Seq_No':  str(hdr.sequencenumber),
                                                            'Hop_Count': str(hdr.hop_count + 1)}
                    self.show_routing_table()

                if hdr.messageto == self.componentinstancenumber:  # if we are the destination, send RREP
                    self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RREP,
                                                                                     message_source,
                                                                                     hdr.messageto,
                                                                                     hdr.int_sender,
                                                                                     0, hdr.sequencenumber + 1, -1, 0, self.componentinstancenumber)))
                    return

                if hdr.messageto in self.RoutingTable.keys():  # if the dest is in Routing Table, check the freshness
                    if hdr.sequencenumber <= int(self.RoutingTable[hdr.messageto]['Seq_No']):
                        self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RREQ,
                                                                                          message_source,
                                                                                          hdr.messageto, int(self.RoutingTable[hdr.messageto]['Next_Hop']),
                                                                                          0, hdr.sequencenumber, -1, hdr.hop_count+1, self.componentinstancenumber)))

                        return
                    else:
                        pass

                else:
                    for i in self.NeighbourList: # if the dest is not in routing table, broadcast
                        self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RREQ,
                                                                                                 message_source,
                                                                                                 hdr.messageto,
                                                                                                 int(i),
                                                                                                 0, hdr.sequencenumber, hdr.rreq_id,
                                                                                                 hdr.hop_count, self.componentinstancenumber)))

        if hdr.messagetype == AODV_ABRMessageTypes.RREP:
            self.updateRoutingTableNeighbours()

            if hdr.messagefrom == self.componentinstancenumber: # if source node receives the RREP, routing finishes
                self.RoutingTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                      'Next_Hop': str(hdr.int_sender),
                                                      'Seq_No':  str(hdr.sequencenumber),
                                                      'Hop_Count': str(hdr.hop_count + 1)}
                #self.show_routing_table()
                print('End of Routing')
                return
            else: # forward the RREP, update the Route Table for the dest, also send the OVERHEAR info to the neighbours
                if hdr.messageto not in self.RoutingTable:
                    self.RoutingTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                         'Next_Hop': str(hdr.int_sender),
                                                         'Seq_No': str(hdr.sequencenumber),
                                                         'Hop_Count': str(hdr.hop_count + 1)}
                    #self.show_routing_table()

                hopCount = int(self.RoutingTable[hdr.messageto]['Hop_Count'])
                self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RREP,
                                                                                 message_source,
                                                                                 hdr.messageto,
                                                                                 int(self.RoutingTable[message_source]['Next_Hop']),
                                                                                 0, hdr.sequencenumber, -1, hopCount,
                                                                                 self.componentinstancenumber)))

                for i in self.NeighbourList:
                    if i != int(self.RoutingTable[hdr.messagefrom]['Next_Hop']) and i != int(hdr.int_sender):
                        hopCount = int(self.RoutingTable[hdr.messageto]['Hop_Count'])
                        self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.OVRH,
                                                                                         message_source,
                                                                                         hdr.messageto,
                                                                                         int(i),
                                                                                         0, hdr.sequencenumber, -1, hopCount,
                                                                                         self.componentinstancenumber)))
        if hdr.messagetype == AODV_ABRMessageTypes.OVRH:
            self.updateRoutingTableNeighbours()
            if hdr.messageto in self.AlternateRouteTable.keys(): # if dest is in AlternateRouteTable, check freshness
                route = self.AlternateRouteTable[hdr.messageto]
                if hdr.sequencenumber > int(route['Seq_No']):
                    route['Seq_No'] = hdr.sequencenumber
                elif hdr.sequencenumber == int(route['Seq_No']) and hdr.hop_count < int(route['Hop_Count']):
                    route['Hop_Count'] = hdr.hop_count
                    route['Next_Hop'] = message_source
                else:
                    print('Ignoring duplicate OVERHEAR messages')
                    pass
                self.show_alternate_route_table()
            else:
                if hdr.messageto not in self.RoutingTable: # if the destination is not in Alternate Route table AND in Routing Table, create entry
                    self.AlternateRouteTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                             'Next_Hop': str(hdr.int_sender),
                                                             'Seq_No': str(hdr.sequencenumber),
                                                             'Hop_Count': str(hdr.hop_count + 1)}

                    self.show_alternate_route_table()
                else:
                    #print('if the dest is in Routing Table, no new entry in Alternate Table')
                    pass

        if hdr.messagetype == AODV_ABRMessageTypes.BRRQ:
            self.updateRoutingTableNeighbours()
            global rerr
            if hdr.messagefrom == self.componentinstancenumber: #sending BRRQ to neighbours
                for i in self.NeighbourList:
                    if i != py.toNode:
                        self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.BRRQ,
                                                                                         message_source,
                                                                                         hdr.messageto,
                                                                                         int(i),
                                                                                         0, hdr.sequencenumber, hdr.rreq_id,
                                                                                         hdr.hop_count,
                                                                                         self.componentinstancenumber, py.messagepayload, py.toNode)))

                time.sleep(5) #20
                if rerr == 1:
                    print('********rerr is 1 ***********')
                    self.show_routing_table()
                    self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RERR,
                                                                                     py.messagepayload,
                                                                                     hdr.messageto,
                                                                                     int(self.RoutingTable[py.messagepayload]['Next_Hop']),
                                                                                     0, hdr.sequencenumber, hdr.rreq_id,
                                                                                     hdr.hop_count,
                                                                                     self.componentinstancenumber, py.messagepayload, py.toNode)))

            else:
                #print('Inside brrq for sending back brrp, I am node ', self.componentinstancenumber)
                self.show_alternate_route_table()
                if hdr.messageto in self.AlternateRouteTable.keys() and int(self.AlternateRouteTable[hdr.messageto]['Next_Hop']) != int(hdr.int_sender):
                    rerr = 0
                    #print(self.componentinstancenumber, ' have dest entry in its alternate route table')
                    route = int(self.AlternateRouteTable[hdr.messageto]['Hop_Count']) ##

                    self.RoutingTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                        'Next_Hop': self.AlternateRouteTable[hdr.messageto]['Next_Hop'],
                                                        'Seq_No': str(hdr.sequencenumber),
                                                        'Hop_Count': str(route)}
                    self.show_routing_table()

                    self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.BRRP,
                                                                                     message_source,
                                                                                     hdr.messageto,
                                                                                     message_source,
                                                                                     0, hdr.sequencenumber, hdr.rreq_id,
                                                                                     route,
                                                                                     self.componentinstancenumber, py.messagepayload, py.toNode)))



                elif hdr.messageto in self.RoutingTable.keys() and int(self.RoutingTable[hdr.messageto]['Next_Hop']) != int(hdr.int_sender): ################
                    rerr = 0
                    #print(self.componentinstancenumber, ' have dest entry in its route table')
                    time.sleep(10)
                    self.show_routing_table()
                    route = self.RoutingTable[hdr.messageto]['Hop_Count']
                    self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.BRRP,
                                                                                     message_source,
                                                                                     hdr.messageto,
                                                                                     message_source,
                                                                                     0, hdr.sequencenumber, hdr.rreq_id,
                                                                                     route,
                                                                                     self.componentinstancenumber,
                                                                                     py.messagepayload, py.toNode)))

                else:
                    #print(self.componentinstancenumber, ' not have an entry for the hdr.messageto which is: ', hdr.messageto)
                    pass


        if hdr.messagetype == AODV_ABRMessageTypes.BRRP:
            #print('Inside brrp, I am node', self.componentinstancenumber)
            self.show_routing_table()
            time.sleep(5)

            if hdr.messageto not in self.BBRP_Responses.keys(): #if the bbrq_response[hdr.messageto] is empty, create an entry
                self.BBRP_Responses[hdr.messageto] = {'Int_Sender': str(hdr.int_sender),
                                                      'Hop_Count': str(hdr.hop_count)}
                #self.show_bbrp_responses()

                hopCount = int(self.BBRP_Responses[hdr.messageto]['Hop_Count']) + 1
                hopCount2 = int(self.RoutingTable[py.toNode]['Hop_Count']) + 1

                self.RoutingTable[py.toNode] = {'Dest': str(py.toNode),
                                                'Next_Hop': str(self.BBRP_Responses[hdr.messageto]['Int_Sender']),
                                                'Seq_No': str(hdr.sequencenumber),
                                                'Hop_Count': str(hopCount2)}

                self.RoutingTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                'Next_Hop': str(self.BBRP_Responses[hdr.messageto]['Int_Sender']),
                                                 'Seq_No': str(hdr.sequencenumber),
                                                 'Hop_Count': str(hopCount)}
                self.show_routing_table()
            else:
                if int(self.BBRP_Responses[hdr.messageto]['Hop_Count']) > int(hdr.hop_count): # if the received brrp response is better
                    self.BBRP_Responses[py.toNode] = {'Int_Sender': str(hdr.int_sender),
                                                      'Hop_Count': str(hdr.hop_count)}
                    #self.show_bbrp_responses()
                else:
                    #print('if the received brrp response is the same')
                    pass

                hopCount = int(self.BBRP_Responses[hdr.messageto]['Hop_Count']) + 1

                self.RoutingTable[hdr.messageto] = {'Dest': str(hdr.messageto),
                                                'Next_Hop': str(self.BBRP_Responses[hdr.messageto]['Int_Sender']),
                                                 'Seq_No': str(hdr.sequencenumber),
                                                 'Hop_Count': str(hopCount)}

                self.show_routing_table()

        if hdr.messagetype == AODV_ABRMessageTypes.RERR:

            if hdr.messagefrom == self.componentinstancenumber:
                print('I am node ', self.componentinstancenumber, ' and restarting RREQ after receiving RERR'),
                for i in self.NeighbourList:
                    self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RREQ,
                                                                                     py.messagepayload,
                                                                                     hdr.messageto,
                                                                                     int(i),
                                                                                     0, hdr.sequencenumber+1, hdr.rreq_id +1,
                                                                                     0,
                                                                                     self.componentinstancenumber)))
            else:
                print('hello from RERR, I am node', self.componentinstancenumber, ' and forwarding RERR message to the node ', py.messagepayload)
                self.show_routing_table()
                self.send_down(Event(self, EventTypes.MFRT, self.prepare_message(AODV_ABRMessageTypes.RERR,
                                                                                 py.messagepayload,
                                                                                 hdr.messageto,
                                                                                 int(self.RoutingTable[py.messagepayload]['Next_Hop']),
                                                                                 0, hdr.sequencenumber,
                                                                                 hdr.rreq_id,
                                                                                 hdr.hop_count,
                                                                                 self.componentinstancenumber)))

    def start_routing(self, src_node, dest_node):
        print('Starting AODV-ABR Routing from node', src_node.componentinstancenumber, 'to node ',
              dest_node.componentinstancenumber)
        self.send_self(Event(self, EventTypes.MFRB,
                             self.prepare_message(AODV_ABRMessageTypes.RREQ, self.componentinstancenumber,
                                                  dest_node.componentinstancenumber, self.componentinstancenumber, 0, 1, 1, 1,  0, self.componentinstancenumber)))

    def prepare_message(self, message_type: AODV_ABRMessageTypes, source: int, dest: int, next_hop:int, int_id:int, seq_number:int, rreq_id:int, hop_count:int,
                        int_sender: int, payload: str = None, payload2: str = None) -> GenericMessage:
        header = AODV_ABRMessageHeader(message_type, source, dest, next_hop, int_id, seq_number, rreq_id, hop_count, int_sender )
        payload = AODV_ABRMessagePayload(payload, payload2)
        return GenericMessage(header, payload)

    def show_routing_table(self):
        print('Routing Table of:', self.componentinstancenumber)
        for key, value in self.RoutingTable.items():
            print(key, ' : ', value)

    def show_alternate_route_table(self):
        print('Alternate Route Table of:', self.componentinstancenumber)
        for key, value in self.AlternateRouteTable.items():
            print(key, ' : ', value)

    def show_bbrp_responses(self):
        print('BBRP Responses of: ', self.componentinstancenumber)
        for key, value in self.BBRP_Responses.items():
            print(key, ' : ', value)

    def show_neighbours(self):
        print('Neighbours:')
        for x in range(len(self.NeighbourList)):
            print(self.NeighbourList[x])

    def updateRoutingTableNeighbours(self):
        for x in self.NeighbourList:
            self.RoutingTable[x] = {'Dest': str(x),
                                    'Next_Hop': str(x),
                                    'Seq_No': 100,
                                    'Hop_Count': 1}

    def linkBreak(self, fromNode, toNode, src_node, dest_node):
        print('Link Break Scenario, Link Break between nodes ', fromNode.componentinstancenumber, ' - ', toNode.componentinstancenumber)
        self.send_self(Event(self, EventTypes.MFRB,
                             self.prepare_message(AODV_ABRMessageTypes.BRRQ, fromNode.componentinstancenumber,
                                                  dest_node.componentinstancenumber, fromNode.componentinstancenumber, 0,
                                                  3, 2, 0, fromNode.componentinstancenumber, src_node.componentinstancenumber, toNode.componentinstancenumber)))


