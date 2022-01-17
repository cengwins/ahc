from enum import Enum
from ahc.Ahc import ComponentModel, Event
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from ahc.Ahc import Topology
registry = ComponentRegistry()

# define your own message types
class ApplicationLayerMessageTypes(Enum):
  PROPOSE = "PROPOSE"
  ACCEPT = "ACCEPT"
  WAVE = "WAVE"
  ACCEPT_WAVE = "ACCEPT_WAVE"
  FINISH_WAVE = "FINISH_WAVE"

#TODO: message_count can be member variable...
message_count = 0
# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
  pass

class WaveMessagePayload:
  def __init__(self, tag):
    self.tag = tag

topo = Topology()

class ElectionEchoExtinctionComponent(ComponentModel):
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    self.neighbors = topo.G.neighbors(self.componentinstancenumber)
    
    # destination = random.randint(len(Topology.G.nodes))
    # destination = 1
    # hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber, destination)
    # payload = ApplicationLayerMessagePayload("23")
    # proposalmessage = GenericMessage(hdr, payload)
    # randdelay = random.randint(0, 5)
    # time.sleep(randdelay)
    # self.send_self(Event(self, "propose", proposalmessage))

  def on_message_from_bottom(self, eventobj: Event):
    try:
      applmessage = eventobj.eventcontent
      hdr = applmessage.header
      global message_count 
      message_count += 1
      if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      elif hdr.messagetype == ApplicationLayerMessageTypes.WAVE:
        print(f"Node-{self.componentinstancenumber} get message from Node-{hdr.messagefrom} with tag {applmessage.payload.tag}")
        self.wave_message(applmessage.payload, hdr)
      elif hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT_WAVE:
        print(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} is ACCEPT_WAVE")
        self.accept_wave_message(applmessage.payload, hdr)


    except AttributeError:
      print("Attribute Error")

  # print(f"{self.componentname}.{self.componentinstancenumber}: Gotton message {eventobj.content} ")
  # value = eventobj.content.value
  # value += 1
  # newmsg = MessageContent( value )
  # myevent = Event( self, "agree", newmsg )
  # self.trigger_event(myevent)

  def on_propose(self, eventobj: Event):
    destination = 1
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber, destination)
    payload = ApplicationLayerMessagePayload("23")
    proposalmessage = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, proposalmessage))

  def on_agree(self, eventobj: Event):
    print(f"Agreed on {eventobj.eventcontent}")

  def on_timer_expired(self, eventobj: Event):
    pass

#TODO: If you call this before all on_inits, then things will go wrong...
  def initiate_process(self):
    self.neighbors = topo.G.neighbors(self.componentinstancenumber)
    print(f"Process initiated {self.componentinstancenumber}")
    self.initiated = True
    for i in self.neighbors:
      destination = i
      hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
      payload = WaveMessagePayload(self.componentinstancenumber)
      wave_msg = GenericMessage(hdr, payload)
      self.send_down(Event(self, EventTypes.MFRT, wave_msg))

    
#TO DO WRITE CHECK EVERY  ACCEPT_WAV E MESSAGES CAME OR NOT IN ANOTTHER FUNC

  def accept_wave_message(self, payload, hdr):
    self.waitingAccepts.remove(hdr.messagefrom)
    if len(self.waitingAccepts) == 0:
      destination = self.parent 
      hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
      payload = WaveMessagePayload(self.parent)
      wave_msg = GenericMessage(hdr1, payload)
      self.send_down(Event(self, EventTypes.MFRT, wave_msg))

  def wave_message(self, payload, hdr):
    if self.initiated: 
      if payload.tag  > self.parent: 
        self.isWaiting = True
        self.parent = hdr.messagefrom

        for i in self.neighbors:
          destination = i 
          hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
          wave_msg = GenericMessage(hdr1, payload)
          self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          self.waitingAccepts.append(i)
        
      elif self.parent > payload.tag: 
        print(f"Node-{self.componentinstancenumber} says tag=={payload.tag} from Node-{hdr.messagefrom} is not accepted")
        pass
      else: 
        destination = hdr.messagefrom
        hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
        wave_msg = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, wave_msg))
    else: 
      if self.parent != payload.tag:
        self.parent = hdr.messagefrom
        print(f"Node-{self.componentinstancenumber} has new parent Node-{self.parent}")
        for i in self.neighbors:
          if i == hdr.messagefrom: 
            continue
          destination = i 
          hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.WAVE, self.componentinstancenumber, destination)
          wave_msg = GenericMessage(hdr1, payload)
          self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          self.waitingAccepts.append(i)
      else: 
        destination = hdr.messagefrom
        hdr1 = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT_WAVE, self.componentinstancenumber, destination)
        wave_msg = GenericMessage(hdr1, payload)
        self.send_down(Event(self, EventTypes.MFRT, wave_msg))
          

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)

    self.eventhandlers["propose"] = self.on_propose
    self.eventhandlers["agree"] = self.on_agree
    self.eventhandlers["timerexpired"] = self.on_timer_expired
    self.parent = componentinstancenumber
    self.initiated = False
    self.isWaiting = False 

    self.waitingAccepts = []
