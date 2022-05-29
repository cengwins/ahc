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
        logger.info(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        logger.info(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")
        evt.eventcontent.header.messageto = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload + "-" + str(self.componentinstancenumber)
        time.sleep(0.1) # TODO WHAT Should this be?
        self.send_down(evt)  # PINGPONG
    
    def on_startbroadcast(self, eventobj: Event):
        hdr = PingPongApplicationLayerMessageHeader(PingPongApplicationLayerMessageTypes.BROADCAST, self.componentinstancenumber, MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        self.counter = self.counter + 1
        
        payload = "BMSG-" + str(self.counter) + ": " + str(self.componentinstancenumber) 
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        logger.debug(f"{self.componentname}.{self.componentinstancenumber} WILL SEND {str(evt)}")
        self.send_down(evt)
    