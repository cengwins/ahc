
import sys
import os
sys.path.append('/usr/local/lib')
#sys.path.insert(0, os.getcwd())
import time
from ctypes import *
from EttusUsrp.LiquidDspUtils import *
from threading import Thread
from EttusUsrp.LiquidDspOfdmFlexFrameHandler import LiquidDspOfdmFlexFrameHandler
# On MacOS, export DYLD_LIBRARY_PATH=/usr/local/lib for sure!


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
    
