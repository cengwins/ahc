import os
import sys
import time
from enum import Enum
sys.path.insert(0, os.getcwd())

from ahc.Ahc import ComponentModel, Event, Topology
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes

#TODO: message_count has to be a member variable
message_count = 0
registry = ComponentRegistry()

topo = Topology()

# define your own message types
class ApplicationLayerMessageTypes(Enum):
  PROPOSE = "PROPOSE"
  ACCEPT = "ACCEPT"
  ACCEPT2 = "ACCEPT2"
  CONNECT = "CONNECT"
  INITIATE = "INITIATE"
  TEST = "TEST"
  REPORT = "REPORT"
  REJECT = "REJECT"
  
  
class EdgeStatus(Enum): 
  FIND = "FIND"
  FOUND = "FOUND"

class EdgeType(Enum): 
  BASIC = "BASIC_EDGE"
  BRANCH = "BRANCH_EDGE"
  REJECTED = "REJECTED"

# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class InitiateMessagePayload:
  def __init__(self, weight, level, status):
    self.weight = weight
    self.level = level
    self.status = status

class TestMessagePayload:
  def __init__(self, fn, level):
    self.fn = fn
    self.level = level

class ReportMessagePayload: 
  def _init_(self, weight): 
    self.weight = weight 

class ConnectMessagePayload:
  def __init__(self, level):
    self.level = level
# class ConnectMessagePayload: 
#   def _init_(self, fn): 
#     self.fn = fn

class ElectionSpiraComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def on_propose(self, eventobj: Event):
    pass
    
    # destination = random.randint(len(Topology.G.nodes))
    # destination = 1
    # hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber, destination)
    # payload = ApplicationLayerMessagePayload("23")
    # proposalmessage = GenericMessage(hdr, payload)
    # randdelay = random.randint(0, 5)
    # time.sleep(randdelay)
    # self.send_self(Event(self, "propose", proposalmessage))

  def on_message_from_bottom(self, eventobj: Event):
    # try:
    global message_count
    applmessage = eventobj.eventcontent
    hdr = applmessage.header
    message_count += 1
    if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
      print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
    elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT2:
      print(f"Node-{self.componentinstancenumber} is ACCEPTed Node-{hdr.messagefrom}")
      self.accept_message_handler(applmessage.payload, hdr)
    elif hdr.messagetype == ApplicationLayerMessageTypes.CONNECT:
      print(f'Node-{self.componentinstancenumber} wants to be connected with {hdr.messagefrom}')
      self.connect_message_handler(applmessage.payload, hdr)
    elif hdr.messagetype == ApplicationLayerMessageTypes.INITIATE:
      print(f'Node-{self.componentinstancenumber} take a initiate message from {hdr.messagefrom} with values (INITIATE, {applmessage.payload.weight},{applmessage.payload.level},{applmessage.payload.status}') 
      self.initiate_message_handler(applmessage.payload, hdr)
    elif hdr.messagetype == ApplicationLayerMessageTypes.TEST:
      print(f"Node-{self.componentinstancenumber} is TESTed by Node-{hdr.messagefrom}")
      self.test_message_handler(applmessage.payload, hdr)
    elif hdr.messagetype == ApplicationLayerMessageTypes.REJECT:
      print(f"Node-{self.componentinstancenumber} is REJECTed by Node-{hdr.messagefrom}")
      self.reject_message_handler(applmessage.payload, hdr)
    elif hdr.messagetype == ApplicationLayerMessageTypes.REPORT:
      print(f"Node-{self.componentinstancenumber} is REPORTed by Node-{hdr.messagefrom} with weight ===> {applmessage.payload.weight}")
      self.report_message_handler(applmessage.payload, hdr)

    # except AttributeError:
    #   print("Attribute Error")

  def get_edge_weight_with_node(self, node): 
    for i in self.basic_edges + self.branch_edges:
      if i[0] == node or i[1] == node:
        return i[2]
    
    return -1 
  
  def get_edge_with_node(self, node): 
    for i in self.weights:
      if i[0] == node or i[1] == node:
        return i
    return

  def find_lowest_weight_node(self):
    edge = self.basic_edges[0]
    for i in range(1,len(self.basic_edges)):
      if self.basic_edges[i][2] < edge[2]:
        edge = self.basic_edges[i]
      
    return edge 

  def connect_message_handler(self, payload, hdr):
    if payload.level == self.level:
      self.level += 1 
      weight = self.get_edge_weight_with_node(hdr.messagefrom)
      new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.INITIATE, self.componentinstancenumber, hdr.messagefrom)
      new_payload = InitiateMessagePayload(weight, self.level, self.status)
      msg = GenericMessage(new_hdr, new_payload)
      self.send_down(Event(self, EventTypes.MFRT, msg))
    elif payload.level < self.level: 
      weight = self.get_edge_weight_with_node(hdr.messagefrom)
      new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.INITIATE, self.componentinstancenumber, hdr.messagefrom)
      new_payload = InitiateMessagePayload(weight, self.level, self.status)
      msg = GenericMessage(new_hdr, new_payload)
      self.send_down(Event(self, EventTypes.MFRT, msg))

  def initiate_message_handler(self, payload, hdr): 
    self.fn = payload.weight
    self.status = payload.status 
    self.level = payload.level 
    self.parent = hdr.messagefrom
    # for i in self.branch_edges:
    #   if i[0] == hdr.messagefrom or i[1] == hdr.messagefrom:
    #     pass 
    #   else: 
    #     pass
        # new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.INITIATE)
        # new_payload = InitiateMessagePayload(self.fn, self.level, self.status)
        # msg = GenericMessage(new_hdr, new_payload)
        # self.send_down(Event(self, EventTypes.MFRT, msg))

    if payload.status == EdgeStatus.FIND:
      if len(self.basic_edges): 
        test_edge = self.find_lowest_weight_node()
        destination = -1 
        if self.componentinstancenumber == test_edge[0]:
          destination = test_edge[1]
        else: 
          destination = test_edge[0]
        new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.TEST, self.componentinstancenumber, destination)
        new_payload = TestMessagePayload(self.fn, self.level)
        msg = GenericMessage(new_hdr, new_payload)
        self.send_down(Event(self, EventTypes.MFRT, msg))
      else: 
        new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.REPORT, self.componentinstancenumber, hdr.messagefrom)
        new_payload = ReportMessagePayload(1000)
        msg = GenericMessage(new_hdr, new_payload)
        self.send_down(self, EventTypes.MFRT, msg)
    else: 
      pass 
    
  def test_message_handler(self, payload, hdr): 
    while self.level < payload.level:
      time.sleep(1)
    
    if payload.fn == self.fn:
      new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.REJECT, self.componentinstancenumber, hdr.messagefrom)
      new_payload = ApplicationLayerMessagePayload('23')
      msg = GenericMessage(hdr, new_payload)
      self.send_down(Event(self, EventTypes.MFRT, msg))
      return 
    else: 
      new_hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber, hdr.messagefrom)
      new_payload = ApplicationLayerMessagePayload('23')
      msg = GenericMessage(hdr, new_payload)
      self.send_down(Event(self, EventTypes.MFRT, msg))

  def reject_message_handler(self, payload, hdr): 
    edge = self.get_edge_with_node(hdr.messagefrom)
    self.rejected_edges.append(edge)
    self.branch_edges.remove(edge)

  def accept_message_handler(self, payload, hdr): 
    weight = self.get_edge_with_node(hdr.messagefrom)
    self.reported_val = weight
    destination = self.parent
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.REPORT, self.componentinstancenumber, hdr.messagefrom)
    payload = ReportMessagePayload(weight)
    msg = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, msg))

  def report_message_handler(self, payload, hdr): 
    if self.reported_val > payload.weight:
      pass 
    else: 
      edge = self.find_lowest_weight_node()
      destination = -1
      if edge[1] == self.componentinstancenumber: 
        destination = edge[0]
      else:
        destination = edge[1]
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.CONNECT, self.componentinstancenumber, destination)
      payload = ConnectMessagePayload(self.fn)
      msg = GenericMessage(hdr, payload)
      self.send_down(self, EventTypes.MFRT, msg)
    pass 

  def initialize_connect(self): 
    print(f"Node-{self.componentinstancenumber} starts initializing")
    destination = -1
    edge = self.branch_edges[0] 
    if edge[1] == self.componentinstancenumber: 
      destination = edge[0] 
    else: 
      destination = edge[1] 
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.CONNECT, self.componentinstancenumber, destination)
    payload = ConnectMessagePayload(self.level)
    msg = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, msg))

  def on_agree(self, eventobj: Event):
    print(f"Agreed on {eventobj.eventcontent}")

  def on_timer_expired(self, eventobj: Event):
    pass


  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["propose"] = self.on_propose
    self.eventhandlers["agree"] = self.on_agree
    self.eventhandlers["timerexpired"] = self.on_timer_expired
    self.weights = []
    self.status = EdgeStatus.FIND

    for x in list(topo.G.edges.data("weight")): 
        if x[1] == componentinstancenumber or x[0] == componentinstancenumber:
          self.weights.append(x)

    self.branch_edges = [] 
    self.rejected_edges = []
    self.basic_edges = self.weights

    #SEND THE LOWEST WEIGHT EDGE TO BRANCH INITIALLY 
    b1_edge = self.find_lowest_weight_node()
    self.branch_edges.append(b1_edge)
    self.basic_edges.remove(b1_edge)

    self.level = 0 
    self.fn = 0 
    self.parent = componentinstancenumber
    self.reported_val = 1000
