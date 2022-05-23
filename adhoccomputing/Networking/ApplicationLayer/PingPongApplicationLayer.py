import time

from ...Generics import *
from ...GenericModel import GenericModel


# define your own message types
class PingPongApplicationLayerMessageTypes(Enum):
    BROADCAST = "BROADCAST"

# define your own message header structure
class PingPongApplicationLayerMessageHeader(GenericMessageHeader):
    pass


class PingPongApplicationLayerEventTypes(Enum):
    STARTBROADCAST = "startbroadcast"


class PingPongApplicationLayer(GenericModel):
    def on_init(self, eventobj: Event):
        self.counter = 0
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers[PingPongApplicationLayerEventTypes.STARTBROADCAST] = self.on_startbroadcast

    def on_message_from_top(self, eventobj: Event):
    # print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        print(f"I am Node.{self.componentinstancenumber}, received from Node.{eventobj.eventcontent.header.messagefrom} a message: {eventobj.eventcontent.payload}")
        evt.eventcontent.header.messageto = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload + "-" + str(self.componentinstancenumber)
        #print(f"I am {self.componentname}.{self.componentinstancenumber}, sending down eventcontent={eventobj.eventcontent.payload}\n")
        time.sleep(0.1)
        self.send_down(evt)  # PINGPONG
    
    def on_startbroadcast(self, eventobj: Event):
        hdr = PingPongApplicationLayerMessageHeader(PingPongApplicationLayerMessageTypes.BROADCAST, self.componentinstancenumber, MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        self.counter = self.counter + 1
        
        payload = "BMSG-" + str(self.counter) + ": " + str(self.componentinstancenumber) 
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        #time.sleep(0.1)
        self.send_down(evt)
        #print("Starting broadcast", self.componentinstancenumber)
    