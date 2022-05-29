import time

from ...Generics import *
from ...GenericModel import GenericModel

import cv2

# define your own message types
class OpenCVVideoStreamingAppMessageTypes(Enum):
    STREAM = "STREAM"

# define your own message header structure
class OpenCVVideoStreamingAppMessageHeader(GenericMessageHeader):
    pass


class OpenCVVideoStreamingAppEventTypes(Enum):
    STARTSTREAMING = "startstreaming"


class OpenCVVideoStreamingApp(GenericModel):
    WindowName = "AHCStream"
    CV2Timer = 1
    frame=None
    framerate = 20
    def on_init(self, eventobj: Event):
        self.counter = 0
        self.t = AHCTimer(1/self.framerate, self.send_frame)
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers[OpenCVVideoStreamingAppEventTypes.STARTSTREAMING] = self.on_startstreaming


    def on_message_from_top(self, eventobj: Event):
        logger.applog(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        self.frame = eventobj.eventcontent.payload    
        logger.applog(f"{self.componentname}.{self.componentinstancenumber} RECEIVED frame")
        # try:
        #     
        #     #cv2.waitKey(0) & 0xFF 
        #     cv2.waitKey(self.CV2Timer)
        #     #cv2.destroyAllWindows()
        # except:
        #     pass
    def on_exit(self, eventobj: Event):
        logger.applog(f"{self.componentname}.{self.componentinstancenumber} EXITING")
        self.cap.release()
        if self.componentinstancenumber == 1:
            self.out.release()

    def send_frame(self):
        hdr = OpenCVVideoStreamingAppMessageHeader(OpenCVVideoStreamingAppMessageTypes.STREAM, self.componentinstancenumber, MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        ret, frame = self.cap.read()
        payload = frame
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        logger.applog(f"{self.componentname}.{self.componentinstancenumber} WILL SEND frame")
        self.send_down(evt)

    def on_startstreaming(self, eventobj: Event):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3,640)
        self.cap.set(4,480)

        self.t.start()
    