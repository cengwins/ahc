import random
import time

from ...Generics import *
from ...GenericModel import GenericModel
import pickle
import secrets
from threading import Lock
# define your own message types
class MessageSegmentationMessageTypes(Enum):
    MORE = "MORE"
    LAST = "LAST"

# define your own message header structure
class MessageSegmentationHeader(GenericMessageHeader):
    def __init__(self, messagetype, messagefrom, messageto, nexthop=..., interfaceid=..., sequencenumber=-1, fragmentid = None, numberoffragments = None):
        super().__init__(messagetype, messagefrom, messageto, nexthop, interfaceid, sequencenumber)
        self.fragmentid = fragmentid
        self.numberoffragments = numberoffragments
    
    def __str__(self) -> str:
        return super().__str__() + f" FRAGID {self.fragmentid} FRAG# {self.numberoffragments}"
    


# define your own message payload structure
class MessageSegmentationPayload(GenericMessagePayload):
    pass


class MessageSegmentation(GenericModel):
    MSS = 1000
    recvmsgs = {}
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)
        self.mutex = Lock()
        self.initframe = True
        
    def on_init(self, eventobj: Event):
        logger.debug(f"Initializing {self.componentname}.{self.componentinstancenumber}")


    def on_message_from_top(self, eventobj: Event):
        #logger.applog(f"{self.componentname}-{self.componentinstancenumber}")
        #self.mutex.acquire(1)
        try:
            
            fragmentid = secrets.token_bytes(4)
            #fragmentid = "DENE"
            msg = eventobj.eventcontent
            hdr = msg.header
            msgpickled = pickle.dumps(msg)
            #logger.applog(f"{self.componentname}-{self.componentinstancenumber} msgsize {len(msgpickled)}")
            ploads = [msgpickled[i:i+self.MSS] for i in range(0, len(msgpickled), self.MSS)] 
            #logger.applog(f"{len(ploads)}")
            for i in range(len(ploads) -1) :
                seghdr = MessageSegmentationHeader(MessageSegmentationMessageTypes.MORE, hdr.messagefrom, hdr.messageto, sequencenumber=i, fragmentid=fragmentid, numberoffragments=len(ploads))
                segpayload = ploads[i]
                segmsg = GenericMessage(seghdr, segpayload)
                self.send_down(Event(None, EventTypes.MFRT, segmsg))
                time.sleep(0.000001)
            seghdr = MessageSegmentationHeader(MessageSegmentationMessageTypes.LAST, hdr.messagefrom, hdr.messageto, sequencenumber=len(ploads)-1, fragmentid=fragmentid, numberoffragments=len(ploads))
            segpayload = ploads[len(ploads)-1]
            segmsg = GenericMessage(seghdr, segpayload)
            
            self.send_down(Event(None, EventTypes.MFRT, segmsg))
            
        except Exception as ex:
            logger.error(f"Exception {self.componentname}-{self.componentinstancenumber} {ex}")   
        #self.mutex.release()
        #self.send_down(eventobj)

    def on_message_from_bottom(self, eventobj: Event):
        
        msg:GenericMessage = eventobj.eventcontent
        hdr:MessageSegmentationHeader = msg.header
        payload = msg.payload
        #logger.applog(f"{self.componentname}-{self.componentinstancenumber} received {str(hdr)}")
        if hdr.messagetype == MessageSegmentationMessageTypes.MORE:
            try:
                self.recvmsgs [hdr.fragmentid]
            except KeyError as ex:
                self.recvmsgs [hdr.fragmentid] = [None]*hdr.numberoffragments
            self.recvmsgs [hdr.fragmentid][hdr.sequencenumber] = payload
        else:
            if hdr.messagetype == MessageSegmentationMessageTypes.LAST:
                logger.applog(f"{self.componentname}-{self.componentinstancenumber} received {str(hdr)}")
                try:
                    self.recvmsgs [hdr.fragmentid]
                except KeyError as ex:
                    self.recvmsgs [hdr.fragmentid] = [None]*hdr.numberoffragments
                self.recvmsgs [hdr.fragmentid][hdr.sequencenumber] = payload
                if None in self.recvmsgs [hdr.fragmentid]:
                    logger.applog(f"{self.componentname}-{self.componentinstancenumber} received LAST BUT THERE IS GAP")
                else:
                    #for i in range(hdr.numberoffragments):
                    #    logger.applog(f"{self.componentname}-{self.componentinstancenumber} {i} {len(self.recvmsgs [hdr.fragmentid][i])} {hdr.fragmentid}")
                    receivedmsg = b''.join(self.recvmsgs [hdr.fragmentid])
                    try:
                        msgrecv = pickle.loads(receivedmsg)
                    #remove segments
                        self.send_up(Event(None, EventTypes.MFRB, msgrecv))
                    except Exception as ex:
                        logger.error(f"{self.componentname}-{self.componentinstancenumber} {ex} ")



