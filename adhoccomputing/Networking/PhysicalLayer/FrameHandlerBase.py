from ...GenericModel import GenericModel

from .SDRUtils import SDRUtils

from .LiquidDspUtils import *
from enum import Enum
from ...Generics import *
from ctypes import *
import pickle
import numpy as np

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
    if SDRType=="b200":
      from .UhdUtils import AhcUhdUtils
      self.sdrdev = AhcUhdUtils(self.componentinstancenumber)
    else:
      if SDRType=="x115":
        from .BladeRFUtils import BladeRFUtils
        self.sdrdev = BladeRFUtils(self.componentinstancenumber)
      else:
        self.sdrdev = SDRUtils(self.componentinstancenumber)
    self.sdrdev.configureSdr(type=SDRType, sdrconfig=self.usrpconfig)
    self.configure()
    self.eventhandlers[PhyEventTypes.RECV] = self.on_recv

  def on_exit(self, eventobj: Event):
    self.sdrdev.receiveenabled = False
    self.sdrdev.shutdown(0)
    return super().on_exit(eventobj)

  def on_init(self, eventobj: Event):
    logger.debug(f"====> I WILL START RECEIVING SAMPLES :  {self.componentname} - {self.componentinstancenumber}")
    self.sdrdev.receiveenabled = True
    self.sdrdev.start_rx(self.rx_callback, self)
    return super().on_init(eventobj)
        

  def on_recv(self, eventobj: Event):
    logger.debug(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")

    #if eventobj.eventcontent.payload.phyheader.messagefrom != self.componentinstancenumber:
    msg = GenericMessage(eventobj.eventcontent.payload.phyheader, eventobj.eventcontent.payload.phypayload)
    self.send_up(Event(self, EventTypes.MFRB, msg))

  def on_message_from_top(self, eventobj: Event):
# channel receives the input message and will process the message by the process event in the next pipeline stage
# Preserve the event id through the pipeline
    try:
      header  = np.zeros(8, dtype=np.ubyte)
      for i in range(8):
        header[i] = i
      hdr = PhyMessageHeader(PhyMessageTypes.PHYFRAMEDATA, self.componentinstancenumber,MessageDestinationIdentifiers.LINKLAYERBROADCAST)
      pld = PhyMessagePayload(eventobj.eventcontent.header, eventobj.eventcontent.payload )
      msg = GenericMessage(hdr, pld)
      byte_arr_msg = bytearray(pickle.dumps(msg))
      payload_len = len(byte_arr_msg)
      payload = np.frombuffer(byte_arr_msg, dtype=np.ubyte)
      self.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING74 )  # TODO: Check params
      
    except RuntimeError as ex:
      logger.critical(f"exection in pickle {ex}")
