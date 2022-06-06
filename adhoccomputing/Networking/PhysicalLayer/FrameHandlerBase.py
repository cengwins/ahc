from ...GenericModel import GenericModel
import queue
from threading import Thread
from .SDRUtils import SDRUtils
import zlib
from .LiquidDspUtils import *
from enum import Enum
from ...Generics import *
from ctypes import *
import pickle
import numpy as np
import copy
# define your own message types
class PhyMessageTypes(Enum):
  PHYFRAMEDATA = "PHYFRAMEDATA"


class PhyEventTypes(Enum):
  RECV = "recv"
  SEND = "send"


# define your own message header structure
class PhyMessageHeader(GenericMessageHeader):
    pass

class PhyFrame():
  def __init__(self, num_rx_samps, recv_buffer):
    self.num_rx_samps = num_rx_samps
    self.recv_buffer= copy.deepcopy(recv_buffer)
    #self.recv_buffer= recv_buffer
    
# define your own message payload structure
class PhyMessagePayload(GenericMessagePayload):

  def __init__(self, header, payload):
    self.phyheader = header
    self.phypayload = payload


class FrameHandlerBase(GenericModel):
  #SDR type can be b200 or x115 for ettus and bladerf respectively.
  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, usrpconfig=None, num_worker_threads=1, topology=None, framers=None, SDRType="b200"):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    self.frame_in_queue = queue.Queue()  # For speed up, a sparate queue for incoming frames will be used.
    self.frame_out_queue = queue.Queue()  # For speed up, a sparate queue for incoming frames will be used.
    self.t_in = Thread(target=self.frame_in_queue_handler, args=[self.frame_in_queue])
    self.t_in.daemon = True
    self.t_in.start()
    self.t_out = Thread(target=self.frame_out_queue_handler, args=[self.frame_out_queue])
    self.t_out.daemon = True
    self.t_out.start()

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
  

  def frame_out_queue_handler(self, myqueue):
    while not self.terminated:
      eventobj: PhyFrame = myqueue.get()
      #sendermutex.acquire(1)
      recv_buffer= eventobj.eventcontent.recv_buffer
      num_tx_samps= eventobj.eventcontent.num_rx_samps
      #logger.applog(f"{self.componentname} {self.componentinstancenumber} received frame from QUEUE {num_tx_samps}")
      if num_tx_samps == 0:
        num_actual_tx_samps = self.sdrdev.finalize_transmit_samples()
      else:
        num_actual_tx_samps = self.sdrdev.transmit_samples(recv_buffer)

      #print(num_actual_tx_samps, "will sleep ", num_tx_samps / self.sdrdev.tx_rate)
      #time.sleep(num_tx_samps / self.sdrdev.tx_rate)
      #sendermutex.release()
      myqueue.task_done()
    logger.warning(f"{self.componentname} {self.componentinstancenumber} TERMINATED SENDING....")

  def frame_in_queue_handler(self, myqueue):
    while not self.terminated:
      #logger.applog(f"{self.componentname} {self.componentinstancenumber} received frame from sdr")
      eventobj = myqueue.get()
      recv_buffer= eventobj.eventcontent.recv_buffer
      num_rx_samps= eventobj.eventcontent.num_rx_samps
      self.rx_callback(num_rx_samps, recv_buffer)
      myqueue.task_done()

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
      #for i in range(8):
      #  header[i] = i
      hdr = PhyMessageHeader(PhyMessageTypes.PHYFRAMEDATA, self.componentinstancenumber,MessageDestinationIdentifiers.LINKLAYERBROADCAST)
      pld = PhyMessagePayload(eventobj.eventcontent.header, eventobj.eventcontent.payload )
      msg = GenericMessage(hdr, pld)
      
      ##### COMPRESS
      byte_arr_msg = bytearray(zlib.compress(pickle.dumps(msg)))
      payload_len = len(byte_arr_msg)
      payload = np.frombuffer(byte_arr_msg, dtype=np.ubyte)
      self.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING74 )  # TODO: Check params
      #logger.applog(f"Trasmitting {payload_len} bytes")
      
    except Exception as ex:
      logger.critical(f"exection in pickle {ex}")
