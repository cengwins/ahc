import os
import sys
import time
import random
from enum import Enum

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Lock, Thread, Topology, MessageDestinationIdentifiers
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Channels.Channels import P2PFIFOPerfectChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageTypes(Enum):
    HELLO_MESSAGE = "HELLO_MESSAGE"
    USER_MESSAGE = "USER_MESSAGE"
    RREQ_MESSAGE = "RREQ_MESSAGE"
    RREP_MESSAGE = "RREP_MESSAGE"
    RERR_MESSAGE = "RERR_MESSAGE"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
        self.messagetype = messagetype
        self.messagefrom = messagefrom
        self.messageto = messageto
        self.nexthop = nexthop
        self.sender = messagefrom
        self.hopcount = 0
        self.broadcastid = -1
        self.sourcesequencenumber = -1
        self.destinationsequencenumber = -1
        self.feasibledistance = -1 
        self.Tbit = 0
        super(ApplicationLayerMessageHeader, self).__init__(messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1)

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


class ApplicationLayerComponent(ComponentModel):

    #def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1):
    #    super().__init__(componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1)

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        self.broadcastdb = []
        self.routing_table = dict()

        #for testing purpose, initiate some messages
        if self.componentinstancenumber == 0:
            # destination = random.randint(len(Topology.G.nodes))
            destination = 1
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.HELLO_MESSAGE, self.componentinstancenumber,
                                                destination, nexthop=destination)
            payload = ApplicationLayerMessagePayload("23")
            hellomessage = GenericMessage(hdr, payload)
            randdelay = random.randint(0, 5)
            time.sleep(randdelay)
            self.send_self(Event(self, "HELLO_MESSAGE", hellomessage))

        elif self.componentinstancenumber == 2:
            destination = 0
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.RREQ_MESSAGE, self.componentinstancenumber,
                                             destination)
            payload = ApplicationLayerMessagePayload("23")          
            hdr.messagetype = ApplicationLayerMessageTypes.RREQ_MESSAGE
            hdr.messagefrom = self.componentinstancenumber
            hdr.nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
            hdr.messageto = destination
            hdr.sender = self.componentinstancenumber
            hdr.hopcount = 0
            hdr.broadcastid = 0
            hdr.sourcesequencenumber = -1
            hdr.destinationsequencenumber = ""
            hdr.feasibledistance = 0            
            randdelay = random.randint(0, 5)
            time.sleep(randdelay)
            rreqmessage = GenericMessage(hdr, payload)
            self.send_self(Event(self, "RREQ_MESSAGE", rreqmessage))

    def on_message_from_bottom(self, eventobj: Event):
        try:
            applmessage = eventobj.eventcontent
            hdr = applmessage.header
            payload = applmessage.payload

            #self.queue_lock.acquire() # protect message_queue, both component thread and Toueg thread are trying to access data
            #self.message_queue.append((int(hdr.messagefrom), hdr.message_type, payload))
            #self.queue_lock.release()


            if hdr.messagetype == ApplicationLayerMessageTypes.HELLO_MESSAGE:
               print(
                f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")

            elif hdr.messagetype == ApplicationLayerMessageTypes.USER_MESSAGE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")

            elif hdr.messagetype == ApplicationLayerMessageTypes.RREQ_MESSAGE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")

            elif hdr.messagetype == ApplicationLayerMessageTypes.RREP_MESSAGE:
                    print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message") 

            elif hdr.messagetype == ApplicationLayerMessageTypes.RERR_MESSAGE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")

        except AttributeError:
            print("Attribute Error")

    # print(f"{self.componentname}.{self.componentinstancenumber}: Gotton message {eventobj.content} ")
    # value = eventobj.content.value
    # value += 1
    # newmsg = MessageContent( value )
    # myevent = Event( self, "agree", newmsg )
    # self.trigger_event(myevent)

    def update_topology(self):
        Topology().nodecolors[self.componentinstancenumber] = 'r'
        Topology().plot()

    def __init__(self, componentname, componentinstancenumber): 
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers["HELLO_MESSAGE"] = self.on_HelloMessage
        self.eventhandlers["USER_MESSAGE"] = self.on_UserMessage
        self.eventhandlers["RREQ_MESSAGE"] = self.on_RreqMessage
        self.eventhandlers["RREP_MESSAGE"] = self.on_RrepMessage
        self.eventhandlers["RERR_MESSAGE"] = self.on_RerrMessage
        self.eventhandlers["timerexpired"] = self.on_timer_expired
        

    def on_HelloMessage(self, eventobj: Event):
        applmessage = eventobj.eventcontent
        hdr = applmessage.header
        payload = applmessage.payload
        if (hdr.sender not in self.routing_table.keys()):
            destination = hdr.sender
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.HELLO_MESSAGE, self.componentinstancenumber,
                                            destination, self.componentinstancenumber)
            payload = ApplicationLayerMessagePayload("23")
            hellomessage = GenericMessage(hdr, payload)
            self.send_down(Event(self, EventTypes.MFRT, hellomessage))

    def on_UserMessage(self, eventobj: Event):
        print(f"User Message: {eventobj.eventcontent}")

    def on_RreqMessage(self, eventobj: Event):
        print(f"RREQ Message: {eventobj.eventcontent}")
        applmessage = eventobj.eventcontent
        hdr = applmessage.header
        payload = applmessage.payload
        hdr.hopcount = hdr.hopcount + 1
        # Check if we have a route to the source. If we have, see if we need
        # to update it. Specifically, update it only if:
        #
        # 1. The destination sequence number for the route is less than the
        #    originator sequence number in the packet
        # 2. The sequence numbers are equal, but the hop_count in the packet
        #    + 1 is lesser than the one in routing table
        # 3. The sequence number in the routing table is unknown
        #
        # If we don't have a route for the originator, add an entry

        if (hdr.Tbit == 1):
            #forward rreq message immediately
            hdr.hopcount = hdr.hopcount + 1 
            hdr.sender = self.componentinstancenumber
            hdr.messageto = MessageDestinationIdentifiers.NETWORKLAYERBROADCAST
            hdr.nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
            print(
                f"{self.componentinstancenumber} will forward the message to {hdr.messageto} over {hdr.nexthop}")
            broadcastmessage = GenericMessage(hdr, applmessage)
            
            self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))
            if hdr.broadcastid not in self.broadcastdb:
                self.broadcastdb.append(hdr.broadcastid)
        
        else:

            if hdr.messagefrom in self.routing_table.keys():
               route = self.routing_table[hdr.messagefrom]
               if (hdr.feasibledistance < (int(route['feasibledistance']))):
                #start new rreq with T=1 from this node
                   hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.RREQ_MESSAGE, self.componentinstancenumber,
                                                    hdr.messageto)
                   payload = ApplicationLayerMessagePayload("23")

                   
                   hdr.messagetype = ApplicationLayerMessageTypes.RREQ_MESSAGE
                   hdr.messagefrom = hdr.messagefrom
                   hdr.nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
                   hdr.messageto = hdr.messageto
                   hdr.sender = self.componentinstancenumber
                   hdr.hopcount = 0
                   hdr.broadcastid = hdr.broadcastid + 1
                   hdr.sourcesequencenumber =  hdr.sourcesequencenumber + 1
                   hdr.destinationsequencenumber = ""
                   hdr.feasibledistance = 0
                   hdr.Tbit = 1
                   
                   rreqmessage = GenericMessage(hdr, payload)
                  
                   self.send_down(Event(self, EventTypes.MFRT, rreqmessage))

               else:
                #send RREP to the source
                    route = self.routing_table[hdr.messagefrom]
                    if (int(route['sequencenumber']) < hdr.sourcesequencenumber):
                        route['sequencenumber'] = hdr.sourcesequencenumber

                    elif (int(route['sequencenumber']) == hdr.sourcesequencenumber):
                        if (int(route['hopcount']) > hdr.hopcount):
                            route['hopcount'] = hdr.hopcount
                            route['nexthop'] = hdr.sender

                    elif (int(route['sequencenumber']) == -1):
                        route['sequencenumber'] = hdr.sourcesequencenumber

                    hdr.messagetype == ApplicationLayerMessageTypes.RREP_MESSAGE
                    hdrmessageto = hdr.messagefrom
                    hdr.messagefrom = self.componentinstancenumber
                    hdr.nexthop = hdr.sender
                    hdr.sender = self.componentinstancenumber
                    hdr.sourcesequencenumber = ""
                    hdr.destinationsequencenumber = hdr.destinationsequencenumber + 1
                    hdr.feasibledistance = int(route['feasibledistance'])
                    hdr.hopcount = 0
                    
                    print(
                        f"{self.componentinstancenumber} will SEND RREP message to {hdr.messageto} over {hdr.nexthop}")
                    RREPmessage = GenericMessage(hdr, applmessage)
                    self.send_down(Event(self, EventTypes.MFRT, RREPmessage))

            else:
                self.routing_table[hdr.messagefrom] = {'Destination': str(hdr.messagefrom), 
                                    'nexthop': str(hdr.sender),
                                    'sequencenumber': str(hdr.sourcesequencenumber),
                                    'feasibledistance': str(hdr.hopcount),
                                    'hopcount': str(hdr.hopcount)}

            if hdr.messageto == self.componentinstancenumber:

               # Check if we are the destination. If we are, generate and send an
               # RREP back.
               #
                 hdr.messagetype == ApplicationLayerMessageTypes.RREP_MESSAGE
                 hdrmessageto = hdr.messagefrom
                 hdr.messagefrom = self.componentinstancenumber
                 hdr.nexthop = hdr.sender
                 hdr.sender = self.componentinstancenumber
                 hdr.sourcesequencenumber = ""
                 hdr.destinationsequencenumber = hdr.destinationsequencenumber + 1
                 hdr.hopcount = 0

                 print(
                     f"{self.componentinstancenumber} will SEND RREP message to {hdr.messageto} over {hdr.nexthop}")
                 RREPmessage = GenericMessage(hdr, applmessage)
                 self.send_down(Event(self, EventTypes.MFRT, RREPmessage))
               
             
            else:

                if hdr.broadcastid in self.broadcastdb:
                  pass  # we have already handled this flooded message
                else:
                  # Forwarding rreq, send to lower layers
                  self.update_topology()
                  hdr.hopcount = hdr.hopcount + 1 
                  hdr.sender = self.componentinstancenumber
                  hdr.messageto = MessageDestinationIdentifiers.NETWORKLAYERBROADCAST
                  hdr.nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
                  print(
                      f"{self.componentinstancenumber} will forward the message to {hdr.messageto} over {hdr.nexthop}")
                  broadcastmessage = GenericMessage(hdr, applmessage)
                  
                  self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))
                  self.broadcastdb.append(hdr.broadcastid)


    def on_RrepMessage(self, eventobj: Event):
        print(f"RREP Message: {eventobj.eventcontent}")
        applmessage = eventobj.eventcontent
        hdr = applmessage.header
        payload = applmessage.payload

        # We are not the destination. Check if we have a valid route
        # to the destination. If we have, generate and send back an
        # RREP.
        #
        if (hdr.messageto in self.routing_table.keys()):
           # Verify that the route is valid and has a higher seq number
           route = self.routing_table[hdr.messageto]
           route_dest_seq_no = int(route['sequencenumber'])
           if (route_dest_seq_no >= hdr.destinationsequencenumber):
              hdr.messagetype == ApplicationLayerMessageTypes.RREP_MESSAGE
              hdr.nexthop = route_dest_seq_no
              hdr.sender = self.componentinstancenumber
              hdr.destinationsequencenumber = route_dest_seq_no
              hdr.hopcount = int(route['hopcount'])

              #print(f"{self.componentinstancenumber} will forward RREP message to {destination} over {nexthop}")
              RREPmessage = GenericMessage(hdr, applmessage)
              self.send_down(Event(self, EventTypes.MFRT, RREPmessage))



    def on_RerrMessage(self, eventobj: Event):
        print(f"RERR Message: {eventobj.eventcontent}")

    def on_timer_expired(self, eventobj: Event):
        pass
        

class LDRnode(ComponentModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        ## the first process does not start immediate, it stars with a peer message
        #if self.componentinstancenumber != 0:
        #    thread = Thread(target=self.job, args=[45, 54, 123])
        #    thread.start()

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):

        # SUBCOMPONENTS
        self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentid)
        self.netlayer = AllSeingEyeNetworkLayer("NetworkLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
        # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
        self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
        # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
        self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

        #self.message_queue = [] # for the next invication clear it...
        #self.queue_lock = Lock()

        super().__init__(componentname, componentid)


    #def job(self, *arg):
    #    self.all_process_ids = []
    #    for element in ComponentRegistry().components:
    #            self.all_process_ids.append(element)
    #    print("Available nodes : ", self.all_process_ids)
    #    self.neighbors = Topology().get_neighbors(self.componentinstancenumber) # retrieve all neighbor ids...


