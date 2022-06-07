import time

from ...Generics import *
from ...GenericModel import GenericModel
import pickle
import cv2

# define your own message types
class OpenCVVideoStreamingAppMessageTypes(Enum):
    STREAM = "STREAM"

# define your own message header structure
class OpenCVVideoStreamingAppMessageHeader(GenericMessageHeader):
    pass


class OpenCVVideoStreamingAppEventTypes(Enum):
    STARTSTREAMING = "startstreaming"

class OpenCVVideoStreamingAppConfig:
    def __init__(self, framerate):
        self.framerate = framerate

class OpenCVVideoStreamingApp(GenericModel):
    WindowName = "AHCStream"
    CV2Timer = 1
    #frame=None
    framerate = 20
    frameheight = 80
    framewidth = 60
    def on_init(self, eventobj: Event):
        self.counter = 0
        
        
        #self.t = AHCTimer(10, self.send_frame)
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        self.config = configurationparameters
        if self.config is not None:
            self.framerate = self.config.framerate
        else:
            self.frame = 1
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers[OpenCVVideoStreamingAppEventTypes.STARTSTREAMING] = self.on_startstreaming
        self.t = AHCTimer(1/self.framerate, self.send_frame)
        self.cap = cv2.VideoCapture(0)
        #self.codec = 0x47504A4D  # MJPG
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('H','2','6','5'))
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('a','v','c','1'))
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'FMP4'))
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPEG'))
        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)
        #self.cap.set(cv2.CAP_PROP_FOURCC, self.codec)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.framewidth)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frameheight)
        logger.applog(f"Video device {str(self.cap)}")
        #self.cap.set(3,self.frameheight)
        #self.cap.set(4,self.framewidth)

            #self.on_startstreaming(eventobj)
        self.initframe = True
        #if self.componentinstancenumber == 1:
        ret, framehighres = self.cap.read()
        framesmallres = cv2.resize(framehighres, (self.frameheight,self.framewidth))
        self.frame =  cv2.cvtColor(framesmallres, cv2.COLOR_BGRA2YUV_I420)

    def on_message_from_top(self, eventobj: Event):
        logger.applog(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        self.frame = pickle.loads(eventobj.eventcontent.payload ) 
        
        #self.frame = eventobj.eventcontent.payload 
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

    def send_frame(self):
        hdr = OpenCVVideoStreamingAppMessageHeader(OpenCVVideoStreamingAppMessageTypes.STREAM, self.componentinstancenumber, MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        ret, framehighres = self.cap.read()
        try:
            framesmallres = cv2.resize(framehighres, (self.frameheight,self.framewidth))
            frame =  cv2.cvtColor(framesmallres, cv2.COLOR_BGR2GRAY)
            #(B,G,R) = cv2.split(frame)
            payload = pickle.dumps(frame)
            if self.initframe == True:
                self.frame = frame   ##### LOOPBACK trials
                self.initframe = False
            #payload = frame.tobytes()
            #logger.applog(f"{self.componentname}-{self.componentinstancenumber}: Payload length {len(payload)}")
            broadcastmessage = GenericMessage(hdr, payload)
            evt = Event(self, EventTypes.MFRT, broadcastmessage)
            #logger.applog(f"{self.componentname}.{self.componentinstancenumber} WILL SEND frame of length {len(payload)}")
            self.send_down(evt)
        except Exception as ex:
            logger.applog(f"{self.componentname}.{self.componentinstancenumber} Exception {ex}")
        

    def on_startstreaming(self, eventobj: Event):
        self.t.start()
    