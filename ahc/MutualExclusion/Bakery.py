#TODO: Component type and hardwired instance numbers are to be corrected
#TODO: Not a good implementation, to be removed
from enum import Enum
import time
from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes
from threading import Thread

node_number = 2
waiting_ticket = [True]*node_number
ticket_values = [0]*node_number
    
class BakeryMessageTypes(Enum):
  INC = "+"
  DEC = "-"

class ResourceComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}\n")
    pass

  def on_message_from_bottom(self, eventobj: Event):
    messagetype = eventobj.eventcontent.header.messagetype ## INC / DEC
    if messagetype == BakeryMessageTypes.INC:
          print("Increment value")
          self.value += 1
    elif messagetype == BakeryMessageTypes.DEC:
          print("Decrement value")
          self.value -= 1
          
  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.value = 0

  def __repr__(self):
    return f"Value:{self.value}"

class MutualExclusionBakeryComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}\n")
    pass

  def send_message(self):
    global flag,turn
    message_header = GenericMessageHeader(self.messageType, self.componentinstancenumber, None,interfaceid=f"{self.componentinstancenumber}-{self.resourceComponentId}")
    message_payload = GenericMessagePayload(None)
    message = GenericMessage(message_header, message_payload)
          
    ticket_values[self.id] = max(ticket_values)+1
    waiting_ticket[self.id] = False
    for i in range(node_number):
      while waiting_ticket[i] == True:
          continue
      while ticket_values[i] > 0 and (ticket_values[i] < ticket_values[self.id] or(ticket_values[i] == ticket_values[self.id] and i < self.id)):
          continue
    ####critical section####
    self.send_down(Event(self, EventTypes.MFRT, message))        
    time.sleep(0.001)
    ########################
    ticket_values[self.id] = 0    
  
    self.done = True

  def __init__(self, componentname, componentinstancenumber,type = BakeryMessageTypes.INC , resourceComponentId = 2):
    super().__init__(componentname, componentinstancenumber)
    self.resourceComponentId = resourceComponentId
    self.done = False
    self.messageType = type
    self.id = self.componentinstancenumber

  def start(self):
    t = Thread(target=self.send_message)
    t.daemon = True
    t.start()
