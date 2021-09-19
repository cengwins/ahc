# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
# 1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
# 3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
# TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)

import sys
import os
<<<<<<< HEAD
from EttusUsrp import LiquidDspUtils
from setuptools._vendor.more_itertools.more import last
=======
>>>>>>> 9d23c3e0ad20e809eefa16ca7863083f52423385
sys.path.append('/usr/local/lib')
# sys.path.append('/opt/local/lib/python3.8/site-packages')
sys.path.insert(0, os.getcwd())
import time
from threading import Thread
import numpy as np
from EttusUsrp.UhdUtils import AhcUhdUtils
from ctypes import *
<<<<<<< HEAD
from EttusUsrp.LiquidDspUtils import *

=======
import pathlib
from EttusUsrp.LiquidDspUtils import *

from PhysicalMediaDependentSubLayer.OfdmPmdComponent import  UsrpB210OfdmPhysicalSubLayer


>>>>>>> 9d23c3e0ad20e809eefa16ca7863083f52423385
# On MacOS, export DYLD_LIBRARY_PATH=/usr/local/lib for sure!

samps_per_est = 100
chan = 0
bandwidth = 250000
freq = 2462000000.0
lo_offset = 0
rate = 4 * bandwidth
wave_freq = 10000
wave_ampl = 0.3
hw_tx_gain = 70.0  # hardware tx antenna gain
hw_rx_gain = 20.0  # hardware rx antenna gain
duration = 1

ahcuhd = AhcUhdUtils()

# ofdmframesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(None))


<<<<<<< HEAD
def ofdm_callback(header:POINTER(struct_c__SA_liquid_float_complex), header_valid, payload, payload_len, payload_valid, stats, userdata) -> c_int32:
    print("ofdm_callback")
    ofdmflexframesync_print(ahcuhd.fs) 
    pass


def rx_callback(num_rx_samps, recv_buffer):
    print(f"recv_callback {num_rx_samps} {len(recv_buffer)}")
    # Calculate power spectral density (frequency domain version of signal)
    # sample_rate = ahcuhd.rx_rate
    # rx_samples = recv_buffer
    # psd = np.abs(np.fft.fftshift(np.fft.fft(rx_samples))) ** 2
    # psd_dB = 10 * np.log10(psd)
    # f = np.linspace(sample_rate / -2, sample_rate / 2, len(psd))
    
    recv_buffer_real = recv_buffer.real
    recv_buffer_imag = recv_buffer.imag
    #print(recv_buffer_real)
    numberofsamplestoprocess = 1
    for j in range(len(recv_buffer)):
        usrp_sample = struct_c__SA_liquid_float_complex(recv_buffer_real[j], recv_buffer_imag[j])
        # usrp_sample.real = recv_buffer_real[j]
        # usrp_sample.imag = recv_buffer_imag[j]
        # print(usrp_sample.real, " + j* ", usrp_sample.imag)
        try:
            if ahcuhd.fs == 0:
                print("fs is null")
            else:
                print("fs is not null", ahcuhd.fs)
            ofdmflexframesync_execute(ahcuhd.fs, usrp_sample, 1);
        except Exception as ex:
            print("Exception", ex)
          
        
def sender_thread(ahcuhd, framer):
    str_header = '12345678'
    hlen = 8
    header = cast(str_header, POINTER(c_ubyte * hlen))[0]
    print("header" ,header)
    str_payload = 'mycontent'
    plen = 9
    payload = cast(str_payload, POINTER(c_ubyte * plen))[0] 
    print("payload", payload)
    
    payload_len = plen
=======
def sender_thread(ahcuhd):
    print("Sender thread initialized")
    data = np.array(
        list(map(lambda n: wave_ampl * ahcuhd.waveforms[ahcuhd.waveform](n, wave_freq, rate),
            np.arange(
                int(10 * np.floor(rate / wave_freq)),
                dtype=np.complex64))),
        dtype=np.complex64)  # One period
    #duration = len(data)/rate
    print(f"Length: {len(data)} rate: {rate} duration: {duration}")
>>>>>>> 9d23c3e0ad20e809eefa16ca7863083f52423385
    while(True): 
        print("will transmit...")
        framer.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128)
        time.sleep(10)


class LiquidDspOfdmFlexFrameHandler(object):
    
    def transmit(self, _header, _payload, _payload_len, _mod, _fec0, _fec1):
        #zerocomplex = liquid_float_complex(0,0)
        #fgbuffer = []
        #for i in range(self.fgbuffer_len):
        #    fgbuffer.append(zerocomplex)
         
        fgbuffer = np.empty(self.fgbuffer_len, dtype=struct_c__SA_liquid_float_complex)   
        self.fgprops.mod_scheme = _mod;
        self.fgprops.fec0 = _fec0;
        self.fgprops.fec1 = _fec1;
        print("a1")
        ofdmflexframegen_setprops(self.fg, byref(self.fgprops));
        print("a2")
        ofdmflexframegen_assemble(self.fg, _header, _payload, _payload_len);
        print("a3")
        last_symbol = False
        while (last_symbol == False):
            print("a4")
            last_symbol = ofdmflexframegen_write(self.fg, fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)), self.fgbuffer_len);
            print("a5", last_symbol, self.fgbuffer_len, type(fgbuffer))
        
            npfgbuffer = np.empty(self.fgbuffer_len, dtype=complex)
            cnt = 0
            for i in fgbuffer.ctypes.data_as(POINTER(struct_c__SA_liquid_float_complex)):
                sample  = i.real+1j*i.imag
                npfgbuffer[cnt] = sample
                cnt = cnt + 1
                if cnt >= self.fgbuffer_len:
                    break
            ahcuhd.transmit_samples(npfgbuffer)
            print("a6")
        ahcuhd.finalize_transmit_samples()
        print("a7")
    def configure(self):
        self.fgprops = ofdmflexframegenprops_s(LIQUID_CRC_32, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128, LIQUID_MODEM_QPSK)
            
        M = c_uint32()
        M = 512
        cp_len = c_uint32()
        cp_len = 64
        taper_len = c_uint32()
        taper_len = 64
        
        self.fgbuffer_len = M + cp_len;
        #self.fgbuffer = np.empty(self.fgbuffer_len, dtype=struct_c__SA_liquid_float_complex)#
        #self.fgbuffer = liquid_float_complex(self.fgbuffer_len)  # TODO: check this EON
        
        
        # fgbuffer = (std::complex<float>*) malloc(fgbuffer_len * sizeof(std::complex<float>));
        res = c_int32()
      
        print(self.fgprops)
        res = ofdmflexframegenprops_init_default(byref(self.fgprops));
        self.fgprops.check = LIQUID_CRC_32
        self.fgprops.fec0 = LIQUID_FEC_NONE
        self.fgprops.fec1 = LIQUID_FEC_HAMMING128
        self.fgprops.mod_scheme = LIQUID_MODEM_QPSK
        self.fg = ofdmflexframegen_create(M, cp_len, taper_len, None, byref(self.fgprops));

        ret = ofdmflexframegen_print(self.fg)
        
        ofdm_callback_function = framesync_callback(ofdm_callback)
        
        try:
            self.fs = ofdmflexframesync_create(M, cp_len, taper_len, None, ofdm_callback_function, None)
            print("fs", self.fs)        
        except Exception as ex:
            print("Exception", ex) 
        
        ahcuhd.set_frame_synch(self.fs)


def main():
    
<<<<<<< HEAD
    # print(LiquidDspUtils.liquiddsp)
    xx = LiquidDspOfdmFlexFrameHandler()
    xx.configure()
    
    ahcuhd.start_rx(rx_callback)

    t = Thread(target=sender_thread, args=[ahcuhd, xx])
=======
    M=c_uint()
    M=256
    cp_len = 16
    taper_len = 16
    res = c_int32()
    
    
    ofdm_pmd = UsrpB210OfdmPhysicalSubLayer("UsrpB210OfdmPhysicalSubLayer", 0)
    ofdm_pmd.configure("winslab_b210_2", M, cp_len, taper_len)
    
    time.sleep(5)
    t = Thread(target=sender_thread, args=[ahcuhd])
>>>>>>> 9d23c3e0ad20e809eefa16ca7863083f52423385
    t.daemon = True
    t.start()
    
    while (True):
        time.sleep(1)
    
    # prevtime = time.time_ns()
    # currbool = False
    # while(True):
    #     #time.sleep(duration/2)
    #     isclear, powerlevel = ahcuhd.ischannelclear()
    #     if (currbool != isclear ):
    #     #if (isclear==False):
    #         currtime = time.time_ns()
    #         print(f"Is the channel clear{isclear}\t {powerlevel}\t{(currtime-prevtime)/1e9}\t {datetime.now()}")
    #         prevtime = currtime
    #     currbool = isclear

        
if __name__ == "__main__":
    main()
    
