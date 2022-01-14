from enum import Enum
import threading
from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, Topology, \
  MessageDestinationIdentifiers, EventTypes
from ahc.Routing.AODV.AODVUtils import AODVMessageTypes, AODVMessageHeader
import random
# define your own message types
class NetworkLayerMessageTypes(Enum):
  NETMSG = "NETMSG"

# define your own message payload structure
class NetworkLayerMessagePayload(GenericMessagePayload):
  pass

class AODVNetworkLayerEventType(Enum):
      RREQ = "RREQ"
      RREP = "RREP"
      PROPOSE = "PROPOSE"

class AODVNetworkLayerComponent(ComponentModel):

  def on_message_from_top(self, eventobj: Event):
    #print(f"On MSFRT {self.componentname}.{self.componentinstancenumber}")
    msg = eventobj.eventcontent
    hdr = msg.header

    if hdr.messagetype == AODVMessageTypes.PROPOSE:
      if hdr.messageto in self.RoutingTable:
        pass
        #self.send_self(Event(self, AODVNetworkLayerEventType.PROPOSE),msg)
      else:
        self.send_self(Event(self, AODVNetworkLayerEventType.RREQ, msg))
    else:
      print(f"Should not be in here {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_bottom(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On MSFRB {self.componentname}.{self.componentinstancenumber}")
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload

    if hdr.messagetype == AODVMessageTypes.RREQ:
      hdr.hopcount += 1
      self.RoutingTable[hdr.messagefrom] = [hdr.messagefrom,hdr.interfaceid,hdr.hopcount,hdr.sequencenumber]
      #print(f"RREQ package received from MFRB")
      self.send_self(Event(self,AODVNetworkLayerEventType.RREQ,msg))
    elif hdr.messagetype == AODVMessageTypes.RREP:
      #print(f"RREP package on route came to {self.componentinstancenumber}")
      self.send_self(Event(self, AODVNetworkLayerEventType.RREP,msg)) 
    elif hdr.messagetype == AODVMessageTypes.PROPOSE:
      #print(f"PROPOSE package on route came to {self.componentinstancenumber}")
      if hdr.messageto == self.componentinstancenumber: #Data is arrived successfully to the Dest with payload
        self.send_up(Event(self,AODVNetworkLayerEventType.PROPOSE,msg))
      else: #Continue to forward
        self.send_self(Event(self,AODVMessageTypes.PROPOSE,msg))  
    self.lock.release()

  #Route Discovery: route request
  def on_rreq(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On {eventobj.eventcontent.header.messagetype} {self.componentname}.{self.componentinstancenumber}")
    msg = eventobj.eventcontent
    hdr = msg.header

    neighbors = Topology().get_neighbors(self.componentinstancenumber)

    #if hdr.messagefrom not in self.RoutingTable:
      #if hdr.messagetype == AODVMessageTypes.RREQ:
      #  hdr.hopcount += 1
      #  self.RoutingTable[hdr.messagefrom] = [hdr.messagefrom,hdr.interfaceid,hdr.hopcount,hdr.sequencenumber]
    if hdr.messageto == self.componentinstancenumber:  #Prepare RREP because RREQ came to the destination.
      print(f"--- RREQ reached destination from {hdr.messagefrom} to {hdr.messageto} , msg type {hdr.messagetype} --- ")
      print(f"RoutingTable: {self.RoutingTable} and my ID: {self.componentinstancenumber}")
      self.send_self(Event(self, AODVNetworkLayerEventType.RREP, msg))
    else: #Node != DestNode so continue RREQ Broadcast
      #Broadcast
      for nexthop in neighbors:
        if nexthop != hdr.interfaceid and hdr.interfaceid != float('inf'):
          #print(f"{self.componentname}.{self.componentinstancenumber} nexthop is {nexthop}")            
          hdr.messagetype = AODVMessageTypes.RREQ
          hdr.nexthop = nexthop
          msg.payload = None
          hdr.interfaceid = self.componentinstancenumber
          self.send_down(Event(self,EventTypes.MFRT,msg))
    #else: #It is in routing table so if sequence number >= the coming package, then RREP if not so continue RREQ.
    #  print(f"Found {hdr.messageto} in Routing Table. TODO") #TODO 

    self.lock.release()

  #Route Discovery: route reply
  def on_rrep(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On rrep {self.componentname}.{self.componentinstancenumber}")
  
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload

    if hdr.messagetype == AODVMessageTypes.RREQ: 
      if self.componentinstancenumber == hdr.messageto: 
        print(f"--- RREP begins from {hdr.messageto} to {hdr.messagefrom} ---")
        hopcount = 0
        destseqnumber = random.randint(0,1000)
        nexthop = hdr.interfaceid
        newhdr = AODVMessageHeader(AODVMessageTypes.RREP, hdr.messageto,hdr.messagefrom
                                ,hopcount,nexthop,self.componentinstancenumber,destseqnumber)
        newmessage = GenericMessage(newhdr, None)
        self.send_down(Event(self,EventTypes.MFRT,newmessage))
      else:
        print(f"Something is wrong on on_rrep")
    elif hdr.messagetype == AODVMessageTypes.RREP:  #RREP packages on route
      #print(f"RREP {self.componentinstancenumber} on {self.componentname} and hdr.messageto {hdr.messageto}")
      if hdr.messageto == self.componentinstancenumber: #RREP arrives at the source finally.
        #print(f"RREP arrives at the {self.componentinstancenumber} on {self.componentname}")
        self.send_up(Event(self,EventTypes.MFRB,msg))
      else: #RREP is on route
        #print(f"{self.componentinstancenumber} routing table: {self.RoutingTable}")
        if hdr.messageto in self.RoutingTable:
          #REVERSE PATH FORWARDING
          #print(f"It is in table so RREP continues")
          hdr.hopcount += 1
          nexthop = self.RoutingTable[hdr.messageto][1] #Nexthop
          self.RoutingTable[hdr.messagefrom] = [hdr.messagefrom,hdr.interfaceid,hdr.hopcount,hdr.sequencenumber]

          newhdr = AODVMessageHeader(AODVMessageTypes.RREP, hdr.messageto,hdr.messagefrom
                                ,hdr.hopcount,nexthop,self.componentinstancenumber,hdr.sequencenumber)
          newmessage = GenericMessage(newhdr, None)
          self.send_down(Event(self,EventTypes.MFRT,newmessage))
        else:
          #TODO
          print(f"Something is wrong RREP should start but {hdr.messagefrom} is not in Routing Table {self.RoutingTable}, my ID {self.componentinstancenumber}")
          print(f"Header info: {hdr}") 
      
    self.lock.release()

  def on_propose(self, eventobj: Event):
    self.lock.acquire()
    #print(f"On_Propose {self.componentname}.{self.componentinstancenumber}")
    msg = eventobj.eventcontent
    hdr = msg.header
    if hdr.messageto in self.RoutingTable: 
      #TODO
      #self.send_down(Event(self,AODVNetworkLayerEventType.PROPOSE,eventobj))
      pass
    self.lock.release()

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    #DestinationNode   NextNode    HopCount     SequenceNumber
    self.RoutingTable = {}
    #self.RoutingTable = { 7:[7,8,3,1] ,
    #                      6: [6,3,5,1]
    #                    }
    self.lock = threading.Lock()
    self.eventhandlers[AODVNetworkLayerEventType.RREQ] = self.on_rreq
    self.eventhandlers[AODVNetworkLayerEventType.RREP] = self.on_rrep
    self.eventhandlers[AODVNetworkLayerEventType.PROPOSE] = self.on_propose
