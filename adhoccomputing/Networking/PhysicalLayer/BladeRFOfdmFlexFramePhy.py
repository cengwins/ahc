from ctypes import *
import pickle
from threading import Lock
from .FrameHandlerBase import *
from ...Generics import *
from .LiquidDspUtils import *
import numpy as np
import time
import struct
mutex = Lock()

framers: FramerObjects = FramerObjects()

#def ofdm_callback(header:POINTER(c_ubyte), header_valid:c_uint32, payload:POINTER(c_ubyte), payload_len:c_uint32, payload_valid:c_int32, stats:struct_c__SA_framesyncstats_s, userdata:POINTER(None)):
def ofdm_callback(header:POINTER(c_ubyte), header_valid:c_int, payload:POINTER(c_ubyte), payload_len:c_uint, payload_valid:c_int, stats:struct_c__SA_framesyncstats_s, userdata:c_void_p ):
    #print("ofdm_callback")
    mutex.acquire(1)
    framer = framers.get_framer_by_id(userdata)
    #print("ofdm_callback", framers, framer.componentinstancenumber)
    #ofdmflexframegen_print(framer.fg)
    # userdata.debug_print()
    #print("Type", type(payload), "Payload Valid?: ", payload_valid, "Length=", payload_len, "payload=", bytes(payload))
    print("RSSI", stats.rssi)
    if payload_valid != 0:
        ofdmflexframesync_print(framer.fs) 
        pload = string_at(payload, payload_len)
        #print("pload=", pload)
        phymsg = pickle.loads(pload)
        #print(phymsg.payload)
        msg = GenericMessage(phymsg.header, phymsg.payload)
        framer.send_self(Event(framer, PhyEventTypes.RECV, msg))
        #print("Header=", msg.header.messagetype, " Payload=", msg.payload, " RSSI=", stats.rssi)   
    #else:
    #    #pass
    #    print("INVALID Type Node", framer.componentinstancenumber, "Payload Valid:[", payload_valid, "]Length=", payload_len, "payload=", bytes(payload))
    #print("RSSI", stats.rssi) 
    mutex.release()
    ofdmflexframesync_reset(framer.fs)
    return 0


  
class BladeRFOfdmFlexFramePhy(FrameHandlerBase):
    
    def on_init(self, eventobj: Event):
        #print("initialize LiquidDspOfdmFlexFrameHandler")
        pass
    
    def rx_callback(self, num_rx_samps, recv_buffer):
        try:
            #print("Self.fs", self.fs)
            #ofdmflexframesync_execute_sc16q11(self.fs, recv_buffer.ctypes.data_as(POINTER(struct_c__SA_liquid_int16_complex)) , num_rx_samps)
            #ofdmflexframesync_execute(self.fs, recv_buffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)) , num_rx_samps)
            ofdmflexframesync_execute_sc16q11(self.fs, recv_buffer , num_rx_samps)
            #print("rx_callback received ", num_rx_samps)
        except Exception as ex:
            print("Exception1", ex)

    
    def transmit(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        
        ofdmflexframegen_assemble(self.fg, _header, _payload, c_uint32(_payload_len))
        last_symbol = 0
        cnt = 0
        while (last_symbol == 0):
            cnt = cnt + 1
            #print("self.fgbuffer.len", self.fgbuffer_len, len(self.fgbuffer))
            last_symbol = ofdmflexframegen_write_sc16q11(self.fg, self.fgbuffer, c_uint32(self.fgbuffer_len))
            
            #last_symbol = ofdmflexframegen_write(self.fg, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)), self.fgbuffer_len)
            #last_symbol = ofdmflexframegen_write(self.fg, self.fgbuffer, c_uint32(self.fgbuffer_len))
            #time.sleep(1)
            #for i in range(self.fgbuffer_len):
                #self.fgbuffer[i] = self.fgbuffer[i] 
            #struct.pack('<h', self.fgbuffer )
            #ofdmflexframesync_execute(self.fs, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)) , self.fgbuffer_len)
            #ofdmflexframesync_execute(self.fs, self.fgbuffer, c_uint32(self.fgbuffer_len))
            #self.rx_callback( c_uint32(self.fgbuffer_len), self.fgbuffer)
            self.sdrdev.transmit_samples(self.fgbuffer)
        
    def configure(self):
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING74, LIQUID_MODEM_QPSK)
        res = ofdmflexframegenprops_init_default(byref(self.fgprops))
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING128
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK

        print("Check", self.fgprops.check)
        print("fec0", self.fgprops.fec0)
        print("fec1", self.fgprops.fec1)
        print("mod_scheme", self.fgprops.mod_scheme)
        
        self.M = (64)
        self.cp_len = (16)
        self.taper_len = (4)
        
        self.fg = ofdmflexframegen_create(self.M, self.cp_len, self.taper_len, None , byref(self.fgprops))
       
        self.fgbuffer_len = 256 # (self.M + self.cp_len)*16
        self.fgbuffer = np.zeros(self.fgbuffer_len*self.sdrdev.bytes_per_sample//sizeof(c_int16), dtype=np.int16)
        #ofdmflexframegen_print(self.fg)
        #a = cast (self.fg, ofdmflexframegen)
        #print(type(a.contents))
        #for field_name, field_type in a.contents._fields_:
        #    print("self.fg.", field_name, getattr(a.contents, field_name))

        res = ofdmflexframegen_print(self.fg)
        
        self.ofdm_callback_function = framesync_callback(ofdm_callback)
        
        try: 
            # WILL PASS ID of THIS OBJECT in userdata then will find the object in FramerObjects
            self.fs :ofdmflexframesync = ofdmflexframesync_create(self.M, self.cp_len, self.taper_len, None, self.ofdm_callback_function, id(self))
            print("fs", self.fs, id(self))   
            framer = self.framers.get_framer_by_id(id(self))
            print("CHEEECK:", self, framer)
        except Exception as ex:
            print("Exception2", ex) 
        
        self.sdrdev.start_rx(self.rx_callback, self)
        ofdmflexframegen_reset(self.fg)
        ofdmflexframesync_reset(self.fs)
        
    # Callbacks have to be outside since the c library does not like "self"
    # Because of this reason will use userdata to get access back to the framer object 

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, usrpconfig=None, num_worker_threads=1, topology=None):
        self.framers = framers
        print("framers=",framers)
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, usrpconfig, num_worker_threads, topology, self.framers, SDRType="x115")
        
