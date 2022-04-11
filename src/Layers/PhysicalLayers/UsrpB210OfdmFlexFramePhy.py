import sys
from ahc.Ahc import Event, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload,MessageDestinationIdentifiers, FramerObjects
from ahc.EttusUsrp.LiquidDspUtils import *
from ahc.EttusUsrp.FrameHandlerBase import FrameHandlerBase, framers, UsrpB210PhyEventTypes
from ctypes import *
import numpy as np
sys.path.append('/usr/local/lib')
import pickle
from threading import Lock
# framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, struct_c__SA_framesyncstats_s, ctypes.POINTER(None))

framers = FramerObjects()

mutex = Lock()
def ofdm_callback(header:POINTER(c_ubyte), header_valid:c_uint32, payload:POINTER(c_ubyte), payload_len:c_uint32, payload_valid:c_int32, stats:struct_c__SA_framesyncstats_s, userdata:POINTER(None)):
    mutex.acquire(1)
    try:
        framer = framers.get_framer_by_id(userdata)
        #print("ofdm_callback", framer.componentinstancenumber)
        #ofdmflexframegen_print(framer.fg)
        # userdata.debug_print()
        #print("Type", type(payload), "Payload Valid?: ", payload_valid, "Length=", payload_len, "payload=", bytes(payload))
        
        if payload_valid != 0:
            #ofdmflexframesync_print(framer.fs) 
            pload = string_at(payload, payload_len)
            #print("pload=", pload)
            phymsg = pickle.loads(pload)
            msg = GenericMessage(phymsg.header, phymsg.payload)
            framer.send_self(Event(framer, UsrpB210PhyEventTypes.RECV, msg))
            #print("Header=", msg.header.messagetype, " Payload=", msg.payload, " RSSI=", stats.rssi)
        #else:
            #pass
        #print("INVALID Type Node", framer.componentinstancenumber, "Payload Valid:[", payload_valid, "]Length=", payload_len, "payload=", bytes(payload))
    
    except Exception as e:
        print("Exception_ofdm_callback:", e)
        print("INVALID Type Node", framer.componentinstancenumber, "Payload Valid:[", payload_valid, "]Length=", payload_len, "payload=", bytes(payload))
    mutex.release()
    return 0

  
class UsrpB210OfdmFlexFramePhy(FrameHandlerBase):
    
    def on_init(self, eventobj: Event):
        #print("initialize LiquidDspOfdmFlexFrameHandler")
        pass
    
    def rx_callback(self, num_rx_samps, recv_buffer):
        try:
            #print("Self.fs", self.fs)
            ofdmflexframesync_execute(self.fs, recv_buffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)) , num_rx_samps)
        except Exception as ex:
            print("Exception1", ex)

    
    def transmit(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        #self.fgprops.mod_scheme = _mod
        #self.fgprops.fec0 = _fec0
        #self.fgprops.fec1 = _fec1
        #ofdmflexframegen_setprops(self.fg, byref(self.fgprops))
        ofdmflexframegen_assemble(self.fg, _header, _payload, _payload_len)
        # print("assembled")
        last_symbol = False
        while (last_symbol == 0):
            fgbuffer = np.zeros(self.fgbuffer_len, dtype=np.complex64)
            
            last_symbol = ofdmflexframegen_write(self.fg, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)), self.fgbuffer_len)
            #for i in range(self.fgbuffer_len):
            #    fgbuffer[i] = fgbuffer[i] * 2
            try:
                self.ahcuhd.transmit_samples(fgbuffer)
                # self.rx_callback(self.fgbuffer_len, npfgbuffer) #loopback for trial
            except Exception as e:
                print("Exception in transmit", e)
        self.ahcuhd.finalize_transmit_samples()
        #ofdmflexframesync_print(self.fs) 
            
        
    def configure(self):
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING74, LIQUID_MODEM_QPSK)
        res = ofdmflexframegenprops_init_default(byref(self.fgprops))
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING74
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        self.fgprops.M = 512
        self.fgprops.cp_len = 64
        self.fgprops.taper_len = 64
        self.fgbuffer_len = self.fgprops.M + self.fgprops.cp_len 

        self.fg = ofdmflexframegen_create(self.fgprops.M, self.fgprops.cp_len, self.fgprops.taper_len, None, byref(self.fgprops))

        res = ofdmflexframegen_print(self.fg)
        
        self.ofdm_callback_function = framesync_callback(ofdm_callback)
        
        try: 
            # WILL PASS ID of THIS OBJECT in userdata then will find the object in FramerObjects
            self.fs = ofdmflexframesync_create(self.fgprops.M, self.fgprops.cp_len, self.fgprops.taper_len, None, self.ofdm_callback_function, id(self))
            print("fs", self.fs, id(self))        
        except Exception as ex:
            print("Exception2", ex) 
        
        self.ahcuhd.start_rx(self.rx_callback, self)
        ofdmflexframegen_reset(self.fg)
        ofdmflexframesync_reset(self.fs)
        

# Callbacks have to be outside since the c library does not like "self"
# Because of this reason will use userdata to get access back to the framer object 

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        
