# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
#1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
#3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
#TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)

import sys
import os
sys.path.append('/usr/local/lib')
#sys.path.append('/opt/local/lib/python3.8/site-packages')
sys.path.insert(0, os.getcwd())
import time
from threading import Thread
import numpy as np
from EttusUsrp.UhdUtils import AhcUhdUtils
import matplotlib.pyplot as plt
import ctypes
from ctypes.util import find_library
import pathlib
from EttusUsrp.LiquidSdrUtils import ofdmflexframegenprops_s

samps_per_est = 100
chan = 0
bandwidth = 250000
freq =2462000000.0
lo_offset = 0
rate=4*bandwidth
wave_freq=10000
wave_ampl = 0.3
hw_tx_gain = 70.0           # hardware tx antenna gain
hw_rx_gain = 20.0           # hardware rx antenna gain
duration = 1

ahcuhd = AhcUhdUtils()

def rx_callback(num_rx_samps, recv_buffer):
    print(f"recv_callback {num_rx_samps} {len(recv_buffer)}")
    # Calculate power spectral density (frequency domain version of signal)
    sample_rate = ahcuhd.rx_rate
    rx_samples = recv_buffer
    psd = np.abs(np.fft.fftshift(np.fft.fft(rx_samples))) ** 2
    psd_dB = 10 * np.log10(psd)
    f = np.linspace(sample_rate / -2, sample_rate / 2, len(psd))

    # Plot time domain
    plt.figure(0)
    plt.plot(np.real(rx_samples[::100]))
    plt.plot(np.imag(rx_samples[::100]))
    plt.xlabel("Time")

    # Plot freq domain
    plt.figure(1)
    plt.plot(f / 1e6, psd_dB)
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("PSD")
    plt.show()
    pass

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
    while(True): 
        #ahcuhd.usrp.send_waveform(data, duration, freq, rate)
        ahcuhd.transmit_samples(data)
        time.sleep(1)

def main():
    libname = find_library("libliquid.dylib")
    print(libname)
    #libname = pathlib.Path().absolute() / "libliquid.dylib"
    liquiddsp = ctypes.CDLL(libname)
    print(liquiddsp)

    aa = liquiddsp.randf()
    print(aa)
    aa = liquiddsp.randf()
    print(aa)
    aa = liquiddsp.randf()
    print(aa)

    fgprops = ofdmflexframegenprops_s()
    fgprops.check = 11

    print(fgprops.check)


    ahcuhd.configureUsrp("winslab_b210_1")
    
    ahcuhd.start_rx(rx_callback)

    t = Thread(target=sender_thread, args=[ahcuhd])
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
    
    
    
    
    