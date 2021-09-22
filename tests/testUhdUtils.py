import sys
import os
sys.path.append('/usr/local/lib')
sys.path.insert(0, os.getcwd())
import time
from EttusUsrp.LiquidDspUtils import *
from threading import Thread
#from EttusUsrp.LiquidDspOfdmFlexFrameHandler import LiquidDspOfdmFlexFrameHandler
from PhysicalMediaDependentSubLayer.UsrpB210OfdmFlexFramePhysicalSubLayer import UsrpB210OfdmFlexFramePhysicalSubLayer
# On MacOS, export DYLD_LIBRARY_PATH=/usr/local/lib for sure!
from ctypes import *


def sender_thread(framer):
    str_header = '12345678'
    hlen = len(str_header)
    #header = cast(str_header, POINTER(c_ubyte * hlen))[0]
    byte_arr_header = bytearray(str_header, 'utf-8')
    header = (c_ubyte*hlen)(*(byte_arr_header))
    str_payload = 'mycontent'
    plen = len(str_payload)
    byte_arr_payload = bytearray(str_payload, 'utf-8')
    payload = (c_ubyte*plen)(*(byte_arr_payload))
    #payload = cast(str_payload, POINTER(c_ubyte * plen))[0] 
    print("Header=", string_at(header,hlen), " Payload=", string_at(payload, plen))
    payload_len = plen

    while(True): 
        # print("will transmit...")
        framer.transmit(header, payload, payload_len, LIQUID_MODEM_QPSK, LIQUID_FEC_NONE, LIQUID_FEC_HAMMING128)
        time.sleep(1)


def main():
    
    ofdmframer = UsrpB210OfdmFlexFramePhysicalSubLayer("UsrpB210OfdmFlexFramePhysicalSubLayer",0)
    ofdmframer.on_init(None) # This will be removed after integrating to AHC
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
    
