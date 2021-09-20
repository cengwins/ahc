# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
# 1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
# 3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
# TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)
#from __future__ import annotations 
import sys
import os
import math
import time
from threading import Thread
import numpy as np
from EttusUsrp.UhdUtils import AhcUhdUtils
from ctypes import *
from EttusUsrp.LiquidDspUtils import *
import inspect
from EttusUsrp.FrameHandlerBase import FrameHandlerBase, framers
# On MacOS, export DYLD_LIBRARY_PATH=/usr/local/lib for sure!

# framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, 
# ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, 
# ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, 
# struct_c__SA_framesyncstats_s, ctypes.POINTER(None))


class LiquidDspOfdmFlexFrameHandler(FrameHandlerBase):
    
    def __init__(self):
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
        self.sw_tx_gain = -12.0 # software gain
        self.duration = 1
        self.ahcuhd = AhcUhdUtils()
        super().__init__()
        

    def debug_print(self):
        print("ok")
    
    def rx_callback(self, num_rx_samps, recv_buffer):
        #print(f"recv_callback {num_rx_samps} {len(recv_buffer)}")
        # Calculate power spectral density (frequency domain version of signal)
        # sample_rate = ahcuhd.rx_rate
        # rx_samples = recv_buffer
        # psd = np.abs(np.fft.fftshift(np.fft.fft(rx_samples))) ** 2
        # psd_dB = 10 * np.log10(psd)
        # f = np.linspace(sample_rate / -2, sample_rate / 2, len(psd))
        #print("Type of buffer:", type(recv_buffer), len(recv_buffer))
        recv_buffer_real = recv_buffer.real
        recv_buffer_imag = recv_buffer.imag
        # print(recv_buffer_real)
        
        #for j in range(len(recv_buffer)):
            #usrp_sample = struct_c__SA_liquid_float_complex(recv_buffer_real[j], recv_buffer_imag[j])
            # usrp_sample.real = recv_buffer_real[j]
            # usrp_sample.imag = recv_buffer_imag[j]
            # print(usrp_sample.real, " + j* ", usrp_sample.imag)
        try:
            # if ahcuhd.fs == 0:
            #    print("fs is null")
            # else:
            #    print("fs is not null", ahcuhd.fs)
            # print("q1", j, usrp_sample.real, usrp_sample.imag)
            ofdmflexframesync_execute(self.fs, recv_buffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)) , num_rx_samps);
            # print("q2", j, usrp_sample.real, usrp_sample.imag)
        except Exception as ex:
            print("Exception1", ex)
    
    def transmit(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        # zerocomplex = liquid_float_complex(0,0)
        # fgbuffer = []
        # for i in range(self.fgbuffer_len):
        #    fgbuffer.append(zerocomplex)    
        self.fgprops.mod_scheme = _mod;
        self.fgprops.fec0 = _fec0;
        self.fgprops.fec1 = _fec1;
        ofdmflexframegen_setprops(self.fg, byref(self.fgprops));
        #print("will assemble")
        ofdmflexframegen_assemble(self.fg, _header, _payload, _payload_len)
        #print("assembled")
        last_symbol = False
        while (last_symbol == 0):
            fgbuffer = np.zeros(self.fgbuffer_len, dtype=np.complex64)
            #fgbuffer = np.zeros(self.fgbuffer_len, dtype=struct_c__SA_liquid_float_complex)
            #fgbuffer = self.fgbuffer_len * struct_c__SA_liquid_float_complex()
            #print("will write", last_symbol)
            last_symbol = ofdmflexframegen_write(self.fg, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)), self.fgbuffer_len);
            #last_symbol = ofdmflexframegen_write(self.fg, fgbuffer, self.fgbuffer_len);
            #print("written", last_symbol)
            #npfgbuffer = np.zeros(self.fgbuffer_len, dtype=np.complex64)
            #cnt = 0
            try:
                #for i in fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)):
                # for i in fgbuffer:
                # #for j in range(self.fgbuffer_len):
                #     #i = fgbuffer[j]
                #     #sample = i.real + 1j * i.imag
                #     sample = i
                #     sample = sample * math.pow(10, self.sw_tx_gain/20)
                #     npfgbuffer[cnt] = sample
                #     cnt = cnt + 1
                #     if cnt >= self.fgbuffer_len:
                #         break
                # print("will transmit samples")
                self.ahcuhd.transmit_samples(fgbuffer)
                #self.rx_callback(self.fgbuffer_len, npfgbuffer) #loopback for trial
                #print("transmitted samples")
            except Exception as e:
                print("Exception in transmit", e)
        #print("finalize_transmit_samples")
        self.ahcuhd.finalize_transmit_samples()
        
    def configure(self):
        
        self.ahcuhd.configureUsrp("winslab_b210_0")
        
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128, LIQUID_MODEM_QPSK)
            
        M = c_uint32()
        M = 256
        cp_len = c_uint32()
        cp_len = 32
        taper_len = c_uint32()
        taper_len = 32
        
        self.fgbuffer_len = M + cp_len;
        res = c_int32()
      
        print(self.fgprops)
        res = ofdmflexframegenprops_init_default(byref(self.fgprops));
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING128
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        self.fg = ofdmflexframegen_create(M, cp_len, taper_len, None, byref(self.fgprops));

        res = ofdmflexframegen_print(self.fg)
        
        self.ofdm_callback_function = framesync_callback(ofdm_callback)
        
        try:
            
            #userdata = c_void_p.from_buffer(py_object(self))
            #userdata = pointer(self)
            #userdata = cast(id(self), c_void_p)
            #print("TYPEEEEE", type(id(self)))
            print("LiquidDspOfdmFlexFrameHandler Framer id=", id(self))
            #self_id = id(self)
            
            #WILL PASS ID of THIS OBJECT in userdata then will find the object in FramerObjects
            self.fs = ofdmflexframesync_create(M, cp_len, taper_len, None, self.ofdm_callback_function, id(self))
            print("fs", self.fs)        
        except Exception as ex:
            print("Exception2", ex) 
        
        
        self.ahcuhd.start_rx(self.rx_callback, self)
        ofdmflexframegen_reset(self.fg);
        ofdmflexframesync_reset(self.fs);


# Callbacks have to be outside since the c library does not like "self"
# Because of this reason will use userdata to get access back to the framer object 

def ofdm_callback( header:POINTER(c_ubyte), header_valid:c_uint32, payload:POINTER(c_ubyte), payload_len:c_uint32, payload_valid:c_int32, stats:struct_c__SA_framesyncstats_s, userdata:POINTER(None)):
    try:
        framer = framers.get_framer_by_id(userdata)
        #print("ofdm_callback", framer)
        #userdata.debug_print()
        ofdmflexframesync_print(framer.fs) 
    except Exception as e:
        print("Exception_ofdm_callback:", e)
    
    return 0

