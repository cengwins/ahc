from ...GenericModel import GenericModel
from .UhdUtils import AhcUhdUtils
from .SDRUtils import SDRUtils
from .BladeRFUtils import BladeRFUtils
from .LiquidDspUtils import *
from enum import Enum
from ...Generics import *
from ctypes import *
import pickle

# define your own message types
class PhyMessageTypes(Enum):
  PHYFRAMEDATA = "PHYFRAMEDATA"


class PhyEventTypes(Enum):
  RECV = "recv"


# define your own message header structure
class PhyMessageHeader(GenericMessageHeader):
    pass


# define your own message payload structure
class PhyMessagePayload(GenericMessagePayload):

  def __init__(self, header, payload):
    self.phyheader = header
    self.phypayload = payload


class FrameHandlerBase(GenericModel):
    #SDR type can be b200 or x115 for ettus and bladerf respectively.
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, usrpconfig=None, num_worker_threads=1, topology=None, framers=None, SDRType="b200"):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.usrpconfig = usrpconfig # should be UsrpConfiguration
        framers.add_framer(id(self), self)
        if type=="b200":
          self.sdrdev = AhcUhdUtils(self.componentinstancenumber)
        else:
          if type=="x115":
            self.sdrdev = BladeRFUtils(self.componentinstancenumber)
          else:
            self.sdrdev = SDRUtils(self.componentinstancenumber)
        self.sdrdev.configureSdr(type=SDRType, sdrconfig=self.usrpconfig)
        self.configure()
        self.eventhandlers[PhyEventTypes.RECV] = self.on_recv

    def on_recv(self, eventobj: Event):
        #print("Node", self.componentinstancenumber, " Received message type:", eventobj.eventcontent.header.messagetype, "  from ", eventobj.eventcontent.payload.phyheader.messagefrom)

        if eventobj.eventcontent.payload.phyheader.messagefrom != self.componentinstancenumber:
          msg = GenericMessage(eventobj.eventcontent.payload.phyheader, eventobj.eventcontent.payload.phypayload)
          self.send_up(Event(self, EventTypes.MFRB, msg))


    def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline

        str_header = "12345678"  #This is the PMD flexframe header. Ourt physical layer header will be concat with the payload below...
        hlen = len(str_header)
        byte_arr_header = bytearray(str_header, 'utf-8')
        header = (c_ubyte * hlen)(*(byte_arr_header))

        hdr = PhyMessageHeader(PhyMessageTypes.PHYFRAMEDATA, self.componentinstancenumber,MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        pld = PhyMessagePayload(eventobj.eventcontent.header, eventobj.eventcontent.payload )
        msg = GenericMessage(hdr, pld)
        byte_arr_msg = bytearray(pickle.dumps(msg))
        plen = len(byte_arr_msg)
        payload = (c_ubyte * plen)(*(byte_arr_msg))
        payload_len = plen
        #print("bytearry:", byte_arr_msg, "Payload:",payload, " payload_len:", payload_len)
        self.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING74 )  # TODO: Check params
        #print("sentpload=", string_at(payload, payload_len))
        #pload = string_at(payload, payload_len)
        #print("pload=", pload)
        #phymsg = pickle.loads(pload)
        #msg2 = GenericMessage(phymsg.header, phymsg.payload)

