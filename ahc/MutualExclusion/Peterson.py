#TODO: Component type and hardwired instance numbers are to be corrected
#TODO: Not a good implementation, to be removed
from enum import Enum
import time
from ahc.Ahc import ComponentModel, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes
from threading import Thread

flag = [False,False]
turn = 0

class PetersonMessageTypes(Enum):
  INC = "+"
  DEC = "-"

class ResourceComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}\n")
    pass

  def on_message_from_bottom(self, eventobj: Event):
    messagetype = eventobj.eventcontent.header.messagetype ## INC / DEC
    if messagetype == PetersonMessageTypes.INC:
          print("Increment value")
          self.value += 1
    elif messagetype == PetersonMessageTypes.DEC:
          print("Decrement value")
          self.value -= 1
          
  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.value = 0

  def __repr__(self):
    return f"Value:{self.value}"

class ProducerConsumerComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}\n")
    pass

  def send_message(self):
    global flag,turn
    message_header = GenericMessageHeader(self.messageType, self.componentinstancenumber, None,interfaceid=f"{self.componentinstancenumber}-{self.resourceComponentId}")
    message_payload = GenericMessagePayload(None)
    message = GenericMessage(message_header, message_payload)
    otherThreadId = 1 - self.id
    for i in range(self.count):
      flag[self.id] = True         # I want to get in to critical section
      turn = otherThreadId         # Lets wait until other thread finish
      while flag[otherThreadId] and turn == otherThreadId:
        time.sleep(0.0000001)
        continue
      ####critical section####
      self.send_down(Event(self, EventTypes.MFRT, message))        
      time.sleep(0.001)
      ########################    
      flag[self.id] = False    # My job is finished

    self.done = True

  def __init__(self, componentname, componentinstancenumber,type = PetersonMessageTypes.INC ,count = 100, resourceComponentId = 2):
    super().__init__(componentname, componentinstancenumber)
    self.count = count
    self.resourceComponentId = resourceComponentId
    self.done = False
    self.messageType = type
    self.id = self.componentinstancenumber

  def start(self):
    t = Thread(target=self.send_message)
    t.daemon = True
    t.start()
