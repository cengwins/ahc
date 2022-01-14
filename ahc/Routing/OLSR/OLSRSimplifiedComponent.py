from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, \
    Thread, Topology
from enum import Enum


class OLSREventTypes(Enum):
    HELLO = "HELLO_MESSAGE"
    TC = "TC_MESSAGE"



class OLSRMessageTypes(Enum):
    GENERATE_HELLO = 'GENERATE_HELLO'
    GENERATE_TC = 'GENERATE_TC'
    HELLO = 'HELLO'
    TC = "TC"
    UPDATE_TABLE="UPDATE_TABLE"


class OLSRSimplifiedRouter(ComponentModel):
    def __init__(self, componentname, componentid):
        super(OLSRSimplifiedRouter, self).__init__(componentname, componentid)
        self.eventhandlers[OLSREventTypes.HELLO] = self.on_hello
        self.eventhandlers[OLSREventTypes.TC] = self.on_tc


        self.duplicateSet = []
        self.linkSet = []
        self.twoHopNeighborSet = []
        self.topologySet = []
        self.neighborSet = []
        self.routingTable=[]
        self.neighbors = Topology().get_neighbors(self.componentinstancenumber)

        self.send_self(Event(self, EventTypes.INIT, None))
    def on_init(self, eventobj: Event):
        super(OLSRSimplifiedRouter, self).on_init(eventobj)
        self.neighborUpdate()

    def neighborUpdate(self):

        for node in self.neighbors:
            self.linkSet.append(node)
        print(self.linkSet)

    def on_message_from_peer(self, eventobj: Event):
        payload = eventobj.eventcontent

        if payload == OLSRMessageTypes.UPDATE_TABLE:
            print('update table')
            self.update_routing_table()
        if payload == OLSRMessageTypes.GENERATE_HELLO:
            print('in hello')
            payload2 = []
            print(self.linkSet)
            for item in self.linkSet:
                print('first for')
                payload2.append(item)
            for node in self.neighborSet:
                print('second for')
                header= OLSRMessageHeader(OLSRSimplifiedRouter.__name__+"-"+self.componentinstancenumber,OLSRMessageTypes.HELLO,
                                           OLSRSimplifiedRouter.__name__+"-"+self.componentinstancenumber,OLSRSimplifiedRouter.__name__ + "-" + str(node),
                                           str(self.componentinstancenumber) + "-" + str(node))
                eventContent = GenericMessage(header, payload2)
                print("sent hello")
                self.send_down(Event(self, EventTypes.MFRT, eventContent))
        if payload == OLSRMessageTypes.GENERATE_TC:
            payload2=[]
            for node in self.linkSet:
                payload2.append(node)
            for neighbor in self.neighborSet:
                header = OLSRMessageHeader(OLSRSimplifiedRouter.__name__ + "-" + self.componentinstancenumber,
                                            OLSRMessageTypes.TC,
                                            OLSRSimplifiedRouter.__name__ + "-" + self.componentinstancenumber,
                                            OLSRSimplifiedRouter.__name__ + "-" + str(node),
                                            str(self.componentinstancenumber) + "-" + str(node))
                eventContent = GenericMessage(header, payload2)
                self.send_down(Event(self, EventTypes.MFRT, eventContent))

    def on_message_from_bottom(self, eventobj: Event):
        print('on message from bottom')
        message = Event.eventcontent
        messageHeader = message.header
        messageContent = message.payload

        if messageContent is None:
            print(f"{self.unique_name()} Message dropped from {messageHeader.messagefrom} is empty.")
            return
        else:
            self.should_message_be_processed(messageContent,messageHeader)
            self.should_message_be_forwarded(messageContent, messageHeader)

    def should_message_be_processed(self, messageHeader,messageContent):
        if any(duplicate.get('D_addr') == messageHeader.originatorAddress and
                duplicate.get('D_seq_num') == messageHeader.messageSequenceNumber for duplicate in self.duplicateSet):
             print(f"{self.unique_name()} Message has not been processed coming from {messageHeader.messagefrom},it has already been processed.")
             return
        if messageHeader.messagetype in OLSRMessageTypes:
            print(
                f"{self.unique_name()} Message will be processed coming from {messageHeader.messagefrom}.")
            self.process_message(messageHeader,messageContent)

    def process_message(self,message_header,message_content):
        msg=GenericMessage(message_header,message_content)
        if message_header.messagetype==OLSRMessageTypes.HELLO: self.send_self(Event(self,OLSREventTypes.HELLO,msg))
        if message_header.messagetype==OLSRMessageTypes.TC: self.send_self(Event(self,OLSREventTypes.TC,msg))
    def forward_message(self,message_header,message_content):
        print('forward message')
        for neighbor in self.neighborSet:
            header = OLSRMessageHeader(message_header.originatoraddress,
                                       OLSRMessageTypes.TC,
                                       OLSRSimplifiedRouter.__name__ + "-" + self.componentinstancenumber,
                                       OLSRSimplifiedRouter.__name__ + "-" + str(neighbor),
                                       str(self.componentinstancenumber) + "-" + str(neighbor))
            eventContent = GenericMessage(header, message_content)
            self.send_down(Event(self, EventTypes.MFRT, eventContent))
    def update_routing_table(self):
        print('update routing table')
        #neighbor tabledakiler
        for node in self.linkSet:
            self.routingTable.append({'R_dest_addr':node,'R_next_addr':node,
                                      'R_dist':1,'R_iface_addr':self.componentinstancenumber})
        for node in self.twoHopNeighborSet:
            index = next(
                i for i, item in enumerate(self.routingTable) if item["R_dest_addr"] == node.N_neighbor_main_addr)
            R_next_addr=self.routingTable[index]['R_next_addr']
            R_iface=self.routingTable[index]['R_iface_addr']
            self.routingTable.append({'R_dest_addr':node.N_neighbor_main_addr,'R_next_addr':R_next_addr,
                                      'R_dist':2,'R_iface_addr':R_iface})
        for entry in self.topologySet:
            if not any(item.get('R_dest_addr')==entry.T_dest_addr for item in self.routingTable) and any(item.get('R_dest_addr')==entry.T_last_addr for
                                                                                                         item in self.routingTable):
                index = next(
                    i for i, item in enumerate(self.routingTable) if item["R_dest_addr"] == entry.T_last_addr)
                h=self.routingTable[index]['R_dist']
                if h>=2:
                    r_next=self.routingTable[index]['R_next_addr']
                    r_face=self.routingTable[index]['R_iface_addr']
                    self.routingTable.append({'R_dest_addr':entry.T_dest_addr,'R_next_addr':r_next,'R_dist':h+1,'R_iface_addr':r_face})
    def on_tc(self, eventobj: Event):
        print('on tc')
        message=eventobj.eventcontent
        hdr=message.header
        payload=message.payload
        if hdr.messagefrom not in self.neighborSet: return
        elif any(item.get('T_last_addr')==hdr.originatoraddress for item in self.topologySet): return
        else:
            for address in payload:
                if any(item.get('T_dest_addr')==address and item.get('T_last_addr')==hdr.originatoraddress for item in self.topologySet):return
                else:
                    self.topologySet.append({'T_dest_addr':address,'T_last_addr':hdr.originatoraddress})
    def on_hello(self, eventobj: Event):
        print('on hello')
        message=eventobj.eventcontent
        payload=message.payload
        hdr=message.header
        if hdr.originatoraddress is self.componentinstancenumber: return
        if hdr.originatoraddress not in self.linkSet:
            self.linkSet.append(hdr.messagefrom)
            self.neighborSet.append(hdr.messagefrom)
        for item in payload:
            if item not in self.neighborSet:
                if not any(element.get('N_neighbor_main_addr')==hdr.originatoraddress and element.get('N_2hop_addr')==item for element in self.twoHopNeighborSet):
                    self.twoHopNeighborSet.append({'N_neighbor_main_addr':hdr.originatoraddress,'N_2hop_addr':item})

    def should_message_be_forwarded(self, messageHeader,messageContent):
        if any(duplicate.get('D_addr') == messageHeader.originatorAddress and
            duplicate.get('D_seq_num') == messageHeader.messageSequenceNumber and
            duplicate.get('D_iface_list')==OLSRSimplifiedRouter.__name__+"-"+self.componentinstancenumber for duplicate in self.duplicateSet):
            print(f"{self.unique_name()} Message will not be forwarded coming from {messageHeader.messagefrom},it has already been considered for forwarding.")
            return

        if messageHeader.messagetype==OLSRMessageTypes.TC:
            self.forward_message(messageHeader,messageContent)
        else:
            self.default_forwarding(messageHeader,messageContent)

    def default_forwarding(self,messageHeader,messageContent):
        if messageHeader.messageto in self.neighborSet:
            msg=GenericMessage(messageHeader,messageContent)
            self.send_down(Event(self,EventTypes.MFRT,msg))
        else:
            return


class OLSRMessageHeader(GenericMessageHeader):
    def __init__(self,  originatoraddress,
                 messagetype, messagefrom, messageto,interface_id ):
        super(OLSRMessageHeader, self).__init__(messagetype, messagefrom, messageto,interfaceid=interface_id)
        self.originatorAddress = originatoraddress


