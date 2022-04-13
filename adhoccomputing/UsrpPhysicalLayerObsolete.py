import sys
sys.path.append('/usr/local/lib')
from Ahc import Event, EventTypes,GenericMessage, GenericMessageHeader,ComponentModel
from enum import Enum
import liquid_usrp_pybind11_wrapper as wrapper

class PhyUsrpB210OFDMPhysicalLayerEventTypes(Enum):
  RECV = "recv"

class PhyUsrpB210OFDMPhysicalLayer(ComponentModel):
  device1 = "winslab_b210_"
  txcvr = None
  ms = wrapper.LIQUID_MODEM_QPSK
  fec0 = wrapper.LIQUID_FEC_NONE  # fec(inner)
  fec1 = wrapper.LIQUID_FEC_GOLAY2412  # fec(outer)

  def mycallback_txcvr(self, header: bytes, headervalid: int, payload: bytes, payloadlen: int, payloadvalid: int, rssi: float,
                        evm: float):
    try:
      #print("mycallback_txcvr1", header, headervalid, payload, payloadlen, payloadvalid, rssi, evm)
      #payload = pickle.load(payload)
      print (payload)
      msg = GenericMessage(GenericMessageHeader("AL", 0, 1), payload)
      self.send_self(Event(self, PhyUsrpB210OFDMPhysicalLayerEventTypes.RECV, msg))

    except Exception as e:
      print("Exception: UnicodeDecodeError {}".format(e))
    return 0

  def on_init(self, eventobj: Event):
    self.device1 = self.device1 + str(self.componentinstancenumber+1)
    M = 512
    cp_len = 64
    taper_len = 64

    self.txcvr = wrapper.ofdmtxrx(self,M, cp_len, taper_len, self.device1)
    #self.txcvr.debug_enable()
    self.txcvr.set_callback(self.mycallback_txcvr)
    self.txcvr.start_rx()
    pass

  def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline
    payload =  eventobj.eventcontent.payload
    #payload = "payloadeon"
    payload_len = len(payload)

    header = "12345678"
    try:
      self.txcvr.transmit_packet_python(header, payload, payload_len, self.ms, self.fec0, self.fec1);
    except Exception as e:
      print("Exception: UnicodeDecodeError {}".format(e))

  def on_recv(self, eventobj: Event):
    print(eventobj.eventcontent.payload)
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers[PhyUsrpB210OFDMPhysicalLayerEventTypes.RECV] = self.on_recv
    # add events here


