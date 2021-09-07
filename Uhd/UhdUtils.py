# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
#1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
#3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
#TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)

import sys
from numpy import power
sys.path.append('/usr/local/lib')
import uhd
import signal
import argparse
import math
import time
from datetime import datetime  
from threading import Thread
import numpy as np

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
duration = 0.1


waveforms = {
    "sine": lambda n, tone_offset, rate: np.exp(n * 2j * np.pi * tone_offset / rate),
    "square": lambda n, tone_offset, rate: np.sign(waveforms["sine"](n, tone_offset, rate)),
    "const": lambda n, tone_offset, rate: 1 + 1j,
    "ramp": lambda n, tone_offset, rate:
            2*(n*(tone_offset/rate) - np.floor(float(0.5 + n*(tone_offset/rate))))
}
waveform = "square"

def get_usrp_power(streamer, num_samps=1000000, chan=0):
    uhd.dsp.signals.get_usrp_power(streamer, num_samps, chan)

def get_streamer(usrp, chan):
    """
    Return an RX streamer with fc32 output
    """
    stream_args = uhd.usrp.StreamArgs('fc32', 'sc16')
    stream_args.channels = [chan]
    return usrp.get_rx_stream(stream_args)

def ischannelclear(usrp, streamer, chan, threshold=-70, pout=100):
    cca_threshold = threshold + 10*math.log10(100/pout)
    tx_rate = usrp.get_rx_rate(chan) / 1e6
    samps_per_est = math.floor(18 * tx_rate)
    power_dbfs = uhd.dsp.signals.get_usrp_power(
          streamer, num_samps=int(samps_per_est), chan=chan)
    if (power_dbfs > cca_threshold ):
        #print(power_dbfs)
        return False, power_dbfs
    else:
        return True, power_dbfs

def sender_thread(usrp):
    print("Sender thread initialized")
    data = np.array(
        list(map(lambda n: wave_ampl * waveforms[waveform](n, wave_freq, rate),
            np.arange(
                int(10 * np.floor(rate / wave_freq)),
                dtype=np.complex64))),
        dtype=np.complex64)  # One period
    duration = len(data)/rate
    print(f"Length: {len(data)} rate: {rate} duration: {duration}")
    while(True): 
        usrp.send_waveform(data, duration, freq, rate)
        time.sleep(1)

def main():
    usrp = uhd.usrp.MultiUSRP(f"type=b200")
    
    usrp.set_rx_bandwidth(bandwidth, chan)
    usrp.set_tx_bandwidth(bandwidth, chan)
    
    usrp.set_rx_freq(freq, chan)
    usrp.set_tx_freq(freq, chan)
    
    usrp.set_rx_bandwidth(bandwidth,chan)
    usrp.set_tx_bandwidth(bandwidth,chan)
    
    usrp.set_rx_rate(rate, chan)
    usrp.set_tx_rate(rate, chan)
    
    usrp.set_rx_gain(hw_rx_gain, chan)
    usrp.set_tx_gain(hw_tx_gain, chan)
    
    
    streamer = get_streamer(usrp, chan)


    t = Thread(target=sender_thread, args=[usrp])
    t.daemon = True
    t.start()
    prevtime = time.time_ns()
    currbool = False
    while(True):
        #time.sleep(duration/2)
        isclear, powerlevel = ischannelclear(usrp, streamer, chan)
        if (currbool != isclear ):
        #if (isclear==False):
            currtime = time.time_ns()
            print(f"Is the channel clear{isclear}\t {powerlevel}\t{(currtime-prevtime)/1e9}\t {datetime.now()}")
            prevtime = currtime
        currbool = isclear
        
if __name__ == "__main__":
    main()
    
    
    
    
    