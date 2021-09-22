from ctypes import *
from enum import Enum
import sys

from Ahc import Event, EventTypes, GenericMessage, GenericMessageHeader, ComponentModel
from EttusUsrp.LiquidDspUtils import *
from EttusUsrp.UhdUtils import AhcUhdUtils
from EttusUsrp.FrameHandlerBase import FrameHandlerBase, framers
import numpy as np
sys.path.append('/usr/local/lib')

# framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, struct_c__SA_framesyncstats_s, ctypes.POINTER(None))


class UsrpB210OfdmFlexFramePhysicalSubLayerEventTypes(Enum):
  RECV = "recv"


def ofdm_callback(header:POINTER(c_ubyte), header_valid:c_uint32, payload:POINTER(c_ubyte), payload_len:c_uint32, payload_valid:c_int32, stats:struct_c__SA_framesyncstats_s, userdata:POINTER(None)):
    try:
        framer = framers.get_framer_by_id(userdata)
        # print("ofdm_callback", framer)
        # userdata.debug_print()
        ofdmflexframesync_print(framer.fs) 
        print("Header=", string_at(header, 8), " Payload=", string_at(payload, payload_len), " RSSI=", stats.rssi)
        msg = GenericMessage(header, payload)
        framer.send_self(Event(framer, UsrpB210OfdmFlexFramePhysicalSubLayerEventTypes.RECV, None))
    except Exception as e:
        print("Exception_ofdm_callback:", e)
    
    return 0

  
class UsrpB210OfdmFlexFramePhysicalSubLayer(FrameHandlerBase):
    
    def on_init(self, eventobj: Event):
        print("initialize LiquidDspOfdmFlexFrameHandler")
        self.samps_per_est = 100
        self.chan = 0
        self.bandwidth = 250000
        self.freq = 2462000000.0
        self.lo_offset = 0
        self.rate = 4 * self.bandwidth
        self.wave_freq = 10000
        self.wave_ampl = 0.3
        self.hw_tx_gain = 70.0  # hardware tx antenna gain
        self.hw_rx_gain = 20.0  # hardware rx antenna gain
        self.sw_tx_gain = -12.0  # software gain
        self.duration = 1
        self.ahcuhd = AhcUhdUtils()
        self.configure()
        

    def on_message_from_top(self, eventobj: Event):
    # channel receives the input message and will process the message by the process event in the next pipeline stage
    # Preserve the event id through the pipeline
        str_header = "12345678"
        hlen = len(str_header)
        byte_arr_header = bytearray(str_header, 'utf-8')
        header = (c_ubyte*hlen)(*(byte_arr_header))
        str_payload = eventobj.eventcontent.payload
        plen = len(str_payload)
        byte_arr_payload = bytearray(str_payload, 'utf-8')
        payload = (c_ubyte*plen)(*(byte_arr_payload))
        #payload = cast(str_payload, POINTER(c_ubyte * plen))[0] 
        print("Header=", string_at(header,hlen), " Payload=", string_at(payload, plen))
        payload_len = plen
        self.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128) #TODO: Check params
            
    
    def rx_callback(self, num_rx_samps, recv_buffer):
        try:
            ofdmflexframesync_execute(self.fs, recv_buffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)) , num_rx_samps);
        except Exception as ex:
            print("Exception1", ex)


    def on_recv(self, eventobj: Event):
        print("Received message", eventobj.eventcontent.payload)
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
    
    def transmit(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        self.fgprops.mod_scheme = _mod;
        self.fgprops.fec0 = _fec0;
        self.fgprops.fec1 = _fec1;
        ofdmflexframegen_setprops(self.fg, byref(self.fgprops));
        ofdmflexframegen_assemble(self.fg, _header, _payload, _payload_len)
        # print("assembled")
        last_symbol = False
        while (last_symbol == 0):
            fgbuffer = np.zeros(self.fgbuffer_len, dtype=np.complex64)
            last_symbol = ofdmflexframegen_write(self.fg, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)), self.fgbuffer_len);
            try:
                self.ahcuhd.transmit_samples(fgbuffer)
                # self.rx_callback(self.fgbuffer_len, npfgbuffer) #loopback for trial
            except Exception as e:
                print("Exception in transmit", e)
        self.ahcuhd.finalize_transmit_samples()
        
    def configure(self):
        
        self.ahcuhd.configureUsrp("winslab_b210_"+str(self.componentinstancenumber))
        
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_GOLAY2412, LIQUID_FEC_GOLAY2412, LIQUID_MODEM_QPSK)
            
        M = 1024
        cp_len = 128
        taper_len = 128        
        self.fgbuffer_len = M + cp_len;
      
        print(self.fgprops)
        res = ofdmflexframegenprops_init_default(byref(self.fgprops));
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_GOLAY2412
        self.fgprops.fec1 = LIQUID_FEC_GOLAY2412
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        self.fg = ofdmflexframegen_create(M, cp_len, taper_len, None, byref(self.fgprops));

        res = ofdmflexframegen_print(self.fg)
        
        self.ofdm_callback_function = framesync_callback(ofdm_callback)
        
        try: 
            # WILL PASS ID of THIS OBJECT in userdata then will find the object in FramerObjects
            self.fs = ofdmflexframesync_create(M, cp_len, taper_len, None, self.ofdm_callback_function, id(self))
            print("fs", self.fs)        
        except Exception as ex:
            print("Exception2", ex) 
        
        self.ahcuhd.start_rx(self.rx_callback, self)
        ofdmflexframegen_reset(self.fg);
        ofdmflexframesync_reset(self.fs);

# Callbacks have to be outside since the c library does not like "self"
# Because of this reason will use userdata to get access back to the framer object 

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[UsrpB210OfdmFlexFramePhysicalSubLayerEventTypes.RECV] = self.on_recv
        
