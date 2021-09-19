from ctypes import *
from enum import Enum
import sys

from Ahc import Event, EventTypes, GenericMessage, GenericMessageHeader, ComponentModel
from EttusUsrp.LiquidDspUtils import *
from EttusUsrp.UhdUtils import AhcUhdUtils

sys.path.append('/usr/local/lib')

#framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, struct_c__SA_framesyncstats_s, ctypes.POINTER(None))
def ofdm_callback(header:POINTER(c_ubyte), header_valid:c_int32, payload:POINTER(c_ubyte), payload_len:c_int32, payload_valid:c_int32, stats:struct_c__SA_framesyncstats_s, userdata:POINTER(None)) -> c_int32:
    print("ofdm_callback")
    ret = c_int32()
    ret = 0
    return ret

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
        
    
    def rx_callback(self, num_rx_samps, recv_buffer):
        print(f"recv_callback {num_rx_samps} {len(recv_buffer)}")
        # Calculate power spectral density (frequency domain version of signal)
        #sample_rate = ahcuhd.rx_rate
        #rx_samples = recv_buffer
        #psd = np.abs(np.fft.fftshift(np.fft.fft(rx_samples))) ** 2
        #psd_dB = 10 * np.log10(psd)
        #f = np.linspace(sample_rate / -2, sample_rate / 2, len(psd))
        
        recv_buffer_real = recv_buffer.real
        recv_buffer_imag = recv_buffer.imag
        #print(recv_buffer_real)
        for j in range(len(recv_buffer)):
            print (j)
            usrp_sample = struct_c__SA_liquid_float_complex(recv_buffer_real[j], recv_buffer_imag[j])
            usrp_sample.real = recv_buffer_real[j]
            usrp_sample.imag = recv_buffer_imag[j]
            #print(usrp_sample.real, " + j* ", usrp_sample.imag)
            #print(usrp_sample)
            try:
                if (self.fs == None):
                    print("Something really bad happened :-)")
                else:
                    print("fs created", self.fs)
                self.liquiddsp.ofdmflexframesync_execute(self.fs, byref(usrp_sample), 1);
            except Exception as e:
                print("Exception", type(e), e, e.args)
                pass
        

    def on_recv(self, eventobj: Event):
        pass
    # print(eventobj.eventcontent.payload)
    # self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
    
    def assemble_frame(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        
        #set properties
        fgprops = ofdmflexframegenprops_s()
        fgprops.mod_scheme = _mod
        fgprops.fec0 = _fec0
        fgprops.fec1 = _fec1
        self.liquiddsp.ofdmflexframegen_setprops(self.fg, byref(self.fgprops))

        #assemble frame
        self.liquiddsp.ofdmflexframegen_assemble(fg, _header, _payload, _payload_len)

    
    def configure(self, device_name, M, cp_len, taper_len):
        self.ahcuhd = AhcUhdUtils()
        self.ahcuhd.configureUsrp(device_name)
        
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128, LIQUID_MODEM_QPSK)
        print(self.fgprops)
        res = self.liquiddsp.ofdmflexframegenprops_init_default(byref(self.fgprops))
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING128
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        self.fg = self.liquiddsp.ofdmflexframegen_create(M, cp_len, taper_len, None, byref(self.fgprops))
    
        print(self.fgprops.check)
        ofdm_callback_function = framesync_callback(ofdm_callback)
        print(ofdm_callback_function.argtypes)
        self.p = c_ubyte(M)
        self.liquiddsp.ofdmframe_init_default_sctype( M, byref(self.p));
        self.fs = self.liquiddsp.ofdmflexframesync_create(M, cp_len, taper_len, byref(self.p), ofdm_callback_function, None)
        if (self.fs == None):
            print("Something really bad happened :-)")
        else:
            print("fs created", self.fs)
        # liquiddsp.ofdmflexframesync_reset(fs);
        
        self.ahcuhd.start_rx(self.rx_callback)

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        self.eventhandlers[UsrpB210OfdmPhysicalSubLayerEventTypes.RECV] = self.on_recv
        self.liquiddsp = CDLL("/usr/local/lib/libliquid.dylib")
        
