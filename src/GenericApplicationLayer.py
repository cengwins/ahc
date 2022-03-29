from generics import *
from GenericModel import GenericModel
from definitions import *
import random
import time 

# define your own message types
class ApplicationLayerMessageTypes(Enum):
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


class GenericApplicationLayer(GenericModel):

    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        if self.componentinstancenumber == 0:
            # destination = random.randint(len(Topology.G.nodes))
            destination = 1
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber,
                                                destination)
            payload = ApplicationLayerMessagePayload("23")
            proposalmessage = GenericMessage(hdr, payload)
            randdelay = random.randint(0, 5)
            time.sleep(randdelay)
            self.send_self(Event(self, "propose", proposalmessage))
        else:
            pass

    def on_message_from_bottom(self, eventobj: Event):
        try:
            applmessage = eventobj.eventcontent
            hdr = applmessage.header
            if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
            elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
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

    def on_propose(self, eventobj: Event):
        destination = 1
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber,
                                            destination)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))

    def on_agree(self, eventobj: Event):
        print(f"Agreed on {eventobj.eventcontent}")

    def on_timer_expired(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers["propose"] = self.on_propose
        self.eventhandlers["agree"] = self.on_agree
        self.eventhandlers["timerexpired"] = self.on_timer_expired

