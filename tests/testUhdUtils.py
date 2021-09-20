# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
# 1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
# 3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
# TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)
#from __future__ import annotations 
import sys
import os
sys.path.append('/usr/local/lib')
sys.path.insert(0, os.getcwd())
import time
from ctypes import *
from EttusUsrp.LiquidDspUtils import *
from threading import Thread
from EttusUsrp.LiquidDspOfdmFlexFrameHandler import LiquidDspOfdmFlexFrameHandler
# On MacOS, export DYLD_LIBRARY_PATH=/usr/local/lib for sure!

# framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, 
# ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, 
# ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, 
# struct_c__SA_framesyncstats_s, ctypes.POINTER(None))

def sender_thread(framer):
    str_header = '12345678'
    hlen = len(str_header)
    header = cast(str_header, POINTER(c_ubyte * hlen))[0]
    print("header" , header)
    str_payload = 'mycontent'
    plen = len(str_payload)
    payload = cast(str_payload, POINTER(c_ubyte * plen))[0] 
    print("payload", payload)
    
    payload_len = plen

    while(True): 
        #print("will transmit...")
        framer.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128)
        time.sleep(1)




def main():
    
    ofdmframer = LiquidDspOfdmFlexFrameHandler()

    ofdmframer.configure()
    
    print("LiquidDspOfdmFlexFrameHandler ofdmframer id=", id(ofdmframer))
    
    t = Thread(target=sender_thread, args=[ofdmframer])
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
    
