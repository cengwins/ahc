import sys
sys.path.append('/usr/local/lib')
from Ahc import Event, EventTypes, GenericMessage, GenericMessageHeader, ComponentModel
from enum import Enum
from EttusUsrp.LiquidDspUtils import *
from EttusUsrp.UhdUtils import AhcUhdUtils
from ctypes import *



def ofdm_callback(self, header, header_valid, payload, payload_len, payload_valid, stats, userdata):
    print("ofdm_callback")
    pass


class UsrpB210OfdmPhysicalSubLayerEventTypes(Enum):
  RECV = "recv"

  
class UsrpB210OfdmPhysicalSubLayer(ComponentModel):
    
    def on_init(self, eventobj: Event):
            pass

    def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline
        payload = eventobj.eventcontent.payload
    # payload = "payloadeon"
        payload_len = len(payload)

        header = "12345678"

    def n_recv(self, eventobj: Event):
    # print(eventobj.eventcontent.payload)
    # self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
    
    

    def configure(self, device_name, M, cp_len, taper_len):
        self.ahcuhd = AhcUhdUtils()
        self.ahcuhd.configureUsrp(device_name)
        
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128, LIQUID_MODEM_QPSK)
        print(self.fgprops)
        res = self.liquiddsp.ofdmflexframegenprops_init_default(byref(self.fgprops));
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING128
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        fg = self.liquiddsp.ofdmflexframegen_create(M, cp_len, taper_len, None, byref(self.fgprops) );
    
        print(self.fgprops.check)
        ofdm_callback_function = framesync_callback(ofdm_callback)
        
        fs = self.liquiddsp.ofdmflexframesync_create(M, cp_len, taper_len, None, ofdm_callback_function, None);
        if (fs == None):
            print("Something really bad happened :-)")
        else:
            print("fs created", fs)
        #liquiddsp.ofdmflexframesync_reset(fs);
        
        self.ahcuhd.start_rx(rx_callback)

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[UsrpB210OfdmPhysicalSubLayerEventTypes.RECV] = self.on_recv
        self.liquiddsp = CDLL("/usr/local/lib/libliquid.dylib")
        