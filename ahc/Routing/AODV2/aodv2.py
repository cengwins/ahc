from numpy import inner
from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, GenericMessagePayload, EventTypes, ComponentRegistry, Lock, Thread, Topology, ConnectorTypes, MessageDestinationIdentifiers
from ahc.Broadcasting.Broadcasting import ControlledFlooding, BroadcastingEventTypes, BroadcastingMessageHeader, BroadcastingMessageTypes
from ahc.Channels.Channels import P2PFIFOFairLossChannel, P2PFIFOPerfectChannel, Channel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer

from enum import Enum

from threading import Lock

import random
import time


inf = float('inf')

class AODVNode(ComponentModel):
   
    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.applicationlayer = ApplicationLayer("ApplicationLayer", componentid)
        self.aodvservice = AODVLayer("AODVLayer", componentid)
        self.linklayer = LinkLayer("LinkLayer", componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.applicationlayer.connect_me_to_component(ConnectorTypes.DOWN, self.aodvservice)
        self.aodvservice.connect_me_to_component(ConnectorTypes.UP, self.applicationlayer)

        self.aodvservice.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
        self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.aodvservice)

        # Connect the bottom component to the composite component....
        self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

        super().__init__(componentname, componentid)

class AODVLayerMessageType(Enum):
    RREQ = "RREQ"
    RREP = "RREP"
    RERR = "RERR"
    DATA = "DATA"

class AODVLayer(ComponentModel):
  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[AODVLayerMessageType.RREQ] = self.on_rreq
    self.eventhandlers[AODVLayerMessageType.RREP] = self.on_rrep
    self.eventhandlers[AODVLayerMessageType.RERR] = self.on_rerr
    self.eventhandlers[AODVLayerMessageType.DATA] = self.on_data
    
    self.rreqLock = Lock() #Lock to prevent simultanious access to db
    self.rrepLock = Lock() #Lock to prevent simultanious access to db

    self.RoutingTable = {}
    
  def on_init(self, eventobj: Event):
    self.uniquebroadcastidentifier = 1
    self.broadcastdb = []
    self.rrepdb = {}
    # if self.componentinstancenumber == 8:
      # self.update_routing_table(4,6,3,1)

  def update_topology(self):
    Topology().nodecolors[self.componentinstancenumber] = 'r'
    # Topology().plot()

  def on_rreq(self, eventobj: Event):
    # self.update_topology()
    applicationLayerMessage = eventobj.eventcontent
    destination = applicationLayerMessage.header.messageto
    source = applicationLayerMessage.header.messagefrom
    sequencenumber = applicationLayerMessage.header.sequencenumber
    self.uniquebroadcastidentifier = self.uniquebroadcastidentifier + 1
    interfaceid = self.uniquebroadcastidentifier
    currentComponent = self.componentinstancenumber
    nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST

    hopCount = self.get_next_hop_count(source, sequencenumber)

    #print(f"Send RREQ Message from {self.componentname}.{self.componentinstancenumber} for destination {destination} over {nexthop}")
    header = AODVBroadcastingMessageHeader(AODVLayerMessageType.RREQ, currentComponent, destination,
                                    nexthop, interfaceid, hopFrom=currentComponent, hopCount=hopCount + 1)
    
    broadcastmessage = AODVBroadcastingMessage(header, applicationLayerMessage)

    self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))

  def on_rrep(self, eventobj: Event):
    # self.update_topology()
    applicationLayerMessage = eventobj.eventcontent
    destination = applicationLayerMessage.header.messageto
    source = applicationLayerMessage.header.messagefrom
    sequencenumber = applicationLayerMessage.header.sequencenumber
    self.uniquebroadcastidentifier = self.uniquebroadcastidentifier + 1
    interfaceid = self.uniquebroadcastidentifier
    currentComponent = self.componentinstancenumber
    nexthop = self.get_next_hop(source, sequencenumber)
    hopCount = self.get_next_hop_count(destination, sequencenumber)

    # print(f"RREP Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for destination {destination} over {nexthop}")
    header = AODVBroadcastingMessageHeader(AODVLayerMessageType.RREP, currentComponent, destination,
                                    nexthop, interfaceid, hopFrom=currentComponent, hopCount=hopCount + 1)
    
    broadcastmessage = AODVBroadcastingMessage(header, applicationLayerMessage)

    self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))

  def on_data(self, eventobj: Event):
    applicationLayerMessage = eventobj.eventcontent
    destination = applicationLayerMessage.header.messageto
    source = applicationLayerMessage.header.messagefrom
    sequencenumber = applicationLayerMessage.header.sequencenumber
    self.uniquebroadcastidentifier = self.uniquebroadcastidentifier + 1
    interfaceid = self.uniquebroadcastidentifier
    currentComponent = self.componentinstancenumber
    nexthop = self.get_next_hop(destination, sequencenumber)

    # print(f"RREP Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for destination {destination} over {nexthop}")
    header = AODVBroadcastingMessageHeader(AODVLayerMessageType.DATA, currentComponent, destination,
                                    nexthop, interfaceid, hopFrom=currentComponent)
    
    broadcastmessage = AODVBroadcastingMessage(header, applicationLayerMessage)

    self.send_down(Event(self, EventTypes.MFRT, broadcastmessage))

  def on_rerr(self, eventobj: Event):
    pass
        
  def on_message_from_top(self, eventobj: Event):
    applicationLayerMessage = eventobj.eventcontent
    applicationLayerMessageHeader = applicationLayerMessage.header
    applicationLayerMessagePayloadDetail = applicationLayerMessage.payload.messagepayload

    source = applicationLayerMessageHeader.messagefrom
    destination = applicationLayerMessageHeader.messageto
    sequencenumber = applicationLayerMessageHeader.sequencenumber

    #Check if destination is in routing table
    nexthop = self.get_next_hop(destination, sequencenumber)

    if(nexthop == inf):
        #If it does not exist in routing table
        #Create RREQ message and broadcast it
        evt = Event(self, AODVLayerMessageType.RREQ, applicationLayerMessage)
        self.send_self(evt)

    else:
        #If it exists in routing table 
        #Send data to destination
        pass

  def on_message_from_bottom(self, eventobj: Event):
    broadcastingMessage = eventobj.eventcontent

    broadcastingMessageHeader = broadcastingMessage.header
    applicationLayerMessage = broadcastingMessage.payload
    applicationLayerMessageHeader = applicationLayerMessage.header

    source = applicationLayerMessageHeader.messagefrom
    destination = broadcastingMessageHeader.messageto
    previousNode = broadcastingMessageHeader.messagefrom
    hopCount = broadcastingMessageHeader.hopCount
    sequencenumber = applicationLayerMessageHeader.sequencenumber

    if broadcastingMessageHeader.messagetype == AODVLayerMessageType.RREQ:
            
      with self.rreqLock:
        if (applicationLayerMessage.uniqueid in self.broadcastdb):
          print(f"RREQ Message Received Already # Receiver: {self.componentname}.{self.componentinstancenumber} from node: {previousNode} with uniqueid {applicationLayerMessage.uniqueid}. Skipping...")

        else:
          self.broadcastdb.append(applicationLayerMessage.uniqueid)
        
          if(source == self.componentinstancenumber):
            print(f"RREQ Message Arrived to Source # Receiver: {self.componentname}.{self.componentinstancenumber} from node: {previousNode} with uniqueid {applicationLayerMessage.uniqueid}. Skipping...")

          else:
            print(f"RREQ Message Received # Receiver: {self.componentname}.{self.componentinstancenumber} from node:{previousNode} for source:{source}")
            self.update_routing_table(source, previousNode, hopCount, sequencenumber)

            self.update_topology()
            if destination == self.componentinstancenumber:
              #RREQ arrived to destination. Send RREP
              time.sleep(random.randint(1, 1))
              print(f"RREP Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
              evt = Event(self, AODVLayerMessageType.RREP, applicationLayerMessage)
              self.send_self(evt)
            
            elif self.get_next_hop(destination, sequencenumber) != inf:
              #Destination is known from routing table, send RREP
              time.sleep(random.randint(1, 1))
              print(f"Node Knows Destination # Receiver: {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
              print(f"RREP Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
              evt = Event(self, AODVLayerMessageType.RREP, applicationLayerMessage)
              self.send_self(evt)
              
            else:
              #Rebroadcast RREQ
              time.sleep(random.randint(1, 1))
              print(f"RREQ Message Resend # Sender: {self.componentname}.{self.componentinstancenumber} for source {source} for destination {destination}")
              evt = Event(self, AODVLayerMessageType.RREQ, applicationLayerMessage)
              self.send_self(evt)
    
    elif broadcastingMessageHeader.messagetype == AODVLayerMessageType.RREP:

      with self.rrepLock:
        if (applicationLayerMessage.uniqueid in self.rrepdb) and (self.rrepdb[applicationLayerMessage.uniqueid]["hopCount"] <= hopCount):
          print(f"RREP Message Received Already # Receiver: {self.componentname}.{self.componentinstancenumber} from node: {previousNode} with uniqueid {applicationLayerMessage.uniqueid}. Skipping...")

        else:
          self.rrepdb[applicationLayerMessage.uniqueid] = {"hopCount": hopCount}
          self.update_routing_table(destination, previousNode, hopCount, sequencenumber)

          if(source == self.componentinstancenumber):
            print(f"RREP Message Arrived to Source # Receiver: {self.componentname}.{self.componentinstancenumber} from {previousNode} with uniqueid {applicationLayerMessage.uniqueid}")
            print(f"DATA Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
            evt = Event(self, AODVLayerMessageType.DATA, applicationLayerMessage)
            self.send_self(evt)
        
          else:
            print(f"Received RREP Message # Receiver: {self.componentname}.{self.componentinstancenumber} from {previousNode} for source {source}")
        
            self.update_topology()
        
            if self.get_next_hop(source, sequencenumber) != inf:
              print(f"RREP Message Send # Sender {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
              evt = Event(self, AODVLayerMessageType.RREP, applicationLayerMessage)
              self.send_self(evt)
            else:
              #If it is not exist in routing table
              pass

    elif broadcastingMessageHeader.messagetype == AODVLayerMessageType.DATA:      
    
      if(destination == self.componentinstancenumber):
        print(f"DATA Message Arrived to Destination # Receiver: {self.componentname}.{self.componentinstancenumber} from {previousNode} with uniqueid {applicationLayerMessage.uniqueid}")
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
    
      else:
        print(f"Received DATA Message # Receiver: {self.componentname}.{self.componentinstancenumber} from {previousNode} for destination {destination}")
    
        if self.get_next_hop(destination, sequencenumber) != inf:
          print(f"DATA Message Send # Sender: {self.componentname}.{self.componentinstancenumber} for source {source} for destionation {destination}")
          evt = Event(self, AODVLayerMessageType.DATA, applicationLayerMessage)
          self.send_self(evt)
        else:
          #If it is not exist in routing table
          pass

  def _get_next_hop_data(self, destination, destinationSequenceNumber):
    try:
      #Routing Table->toId, nextHop, toSeqNum, lifeTime
      retval = self.RoutingTable[destination]
      #TODO if timeout is occured, delete record
      #if not, update timeout
      if(retval["destinationSequenceNumber"] >= destinationSequenceNumber):
        return retval
      else:
        return inf
    except KeyError:
      return inf
    except IndexError:
      return inf

  def get_next_hop(self, destination, destinationSequenceNumber):
    retval = self._get_next_hop_data(destination, destinationSequenceNumber)
    if retval != inf:
      return retval["nextHop"]

    return inf

  def get_next_hop_count(self, destination, destinationSequenceNumber):
    retval = self._get_next_hop_data(destination, destinationSequenceNumber)
    if retval != inf:
      return retval["hopCount"]

    return 0

  def update_routing_table(self, destination, nextHop, hopCount, destinationSequenceNumber):
    retval = inf
    try:
      #Routing Table->toId, nextHop, toSeqNum, lifeTime
      retval = self.RoutingTable[destination]
      #TODO if timeout is occured, delete record
      #if not, update timeout
    except KeyError:
      pass
    except IndexError:
      pass
    
    if((retval == inf) or (hopCount < retval["hopCount"])):
      print(f"Routing Table Updated # Node: {self.componentname}.{self.componentinstancenumber} Data => destination:{destination} nextHop:{nextHop} hopCount:{hopCount} sequenceNumber:{destinationSequenceNumber}")
      # lifeTime da gerekli olabilir
      self.RoutingTable[destination] = {
        "destination": destination,
        "nextHop": nextHop,
        "hopCount": hopCount,
        "destinationSequenceNumber": destinationSequenceNumber
      }
    
class ApplicationLayerMessageTypes(Enum):
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"

# class ApplicationLayerMessageHeader(GenericMessageHeader):
#     pass

# class ApplicationLayerMessagePayload(GenericMessagePayload):
#     pass

class ApplicationLayer(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        # For testing purpose
        #####################
        if self.componentinstancenumber == 0:
            # destination = random.randint(len(Topology.G.nodes))
            destination = 4
            header = AODVApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber, destination, sequencenumber=1)
            payload = AODVApplicationLayerMessagePayload("Test Message")
            message = AODVApplicationLayerMessage(header, payload)
            randdelay = random.randint(3, 5)
            time.sleep(randdelay)
          
            print(f"Message Send # Sender: {self.componentname}.{self.componentinstancenumber} to destination {destination}")
            self.send_down(Event(self, EventTypes.MFRT, message))
        ########################

    def on_message_from_top(self, eventobj: Event):
        print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_bottom(self, eventobj: Event):
        print(f"Message Received # Node: {self.componentname}.{self.componentinstancenumber} Message: {eventobj.eventcontent.payload.payload.messagepayload}")

class AODVChannel(Channel):
  def on_deliver_to_component(self, eventobj: Event):
    message = eventobj.eventcontent
    linklayerMessageHeader = message.header
    broadcastingMessage = message.payload
    broadcastingMessageHeader = broadcastingMessage.header
    applicationLayerMessage = broadcastingMessage.payload

    messageType = broadcastingMessageHeader.messagetype

    if messageType == AODVLayerMessageType.RREQ:
      callername = eventobj.eventsource.componentinstancenumber
      for item in self.connectors:
        callees = self.connectors[item]
        for callee in callees:
          calleename = callee.componentinstancenumber
          
          if calleename == callername:
            pass
          else:
          
            myevent = Event(eventobj.eventsource, EventTypes.MFRB,
                            eventobj.eventcontent, self.componentinstancenumber,
                            eventid=eventobj.eventid)
            callee.trigger_event(myevent)

    elif messageType == AODVLayerMessageType.RREP or messageType == AODVLayerMessageType.DATA:
      nexthop = broadcastingMessageHeader.nexthop
      callername = eventobj.eventsource.componentinstancenumber
      for item in self.connectors:
        callees = self.connectors[item]
        for callee in callees:
          calleename = callee.componentinstancenumber
          
          if calleename == callername:
            pass
          elif calleename == nexthop:
            myevent = Event(eventobj.eventsource, EventTypes.MFRB,
                            eventobj.eventcontent, self.componentinstancenumber,
                            eventid=eventobj.eventid)
            callee.trigger_event(myevent)

class AODVBroadcastingMessageHeader(BroadcastingMessageHeader):
  def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1, hopFrom=None, hopCount=-1):
    super().__init__(messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber)
    self.hopFrom = hopFrom
    self.hopCount = hopCount
  
class AODVBroadcastingMessagePayload(GenericMessagePayload):
  pass

class AODVBroadcastingMessage(GenericMessage):
  pass

class AODVApplicationLayerMessageHeader(GenericMessageHeader):
  pass

class AODVApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class AODVApplicationLayerMessage(GenericMessage):
  pass