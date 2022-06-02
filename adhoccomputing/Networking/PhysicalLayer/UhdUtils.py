# https://www.etsi.org/deliver/etsi_en/300300_300399/300328/02.01.01_60/en_300328v020101p.pdf
#1) Before transmission, the equipment shall perform a Clear Channel Assessment (CCA) check using energy detect. The equipment shall observe the operating channel for the duration of the CCA observation time which shall be not less than 18 μs. The channel shall be considered occupied if the energy level in the channel exceeds the threshold given in step 5 below. If the equipment finds the channel to be clear, it may transmit immediately. See figure 2 below.
#3) The total time during which an equipment has transmissions on a given channel without re-evaluating the availability of that channel, is defined as the Channel Occupancy Time.
# The Channel Occupancy Time shall be in the range 1 ms to 10 ms followed by an Idle Period of at least 5 % of the Channel Occupancy Time used in the equipment for the current Fixed Frame Period.
# The energy detection threshold for the CCA shall be proportional to the transmit power of the transmitter: for a 20 dBm e.i.r.p. transmitter the CCA threshold level (TL) shall be equal to or less than -70 dBm/MHz at the input to the receiver assuming a 0 dBi (receive) antenna assembly. This threshold level (TL) may be corrected for the (receive) antenna assembly gain (G); however, beamforming gain (Y) shall not be taken into account. For power levels less than 20 dBm e.i.r.p. the CCA threshold level may be relaxed to:
#TL = -70 dBm/MHz + 10 × log10 (100 mW / Pout) (Pout in mW e.i.r.p.)


import uhd
import math
from threading import Thread, Lock
import numpy as np
import inspect
import argparse
import inspect
import os
import re
import sys
from .SDRUtils import SDRUtils
from ...Generics import *
from ...Networking.PhysicalLayer.FrameHandlerBase import PhyEventTypes, PhyFrame


class AhcUhdUtils(SDRUtils):
    
    def __init__(self, componentinstancenumber) -> None:
        super().__init__(componentinstancenumber)
        self.mutex = Lock()
        self.cca = False
        self.INIT_DELAY = 0
        if not bool (self.usrps):
            self.probe_usrps()
      
    
    #defaultusrpconfig = SDRConfiguration(freq =915000000.0, bandwidth = 2000000, chan = 0, hw_tx_gain = 50, hw_rx_gain = 20, sw_tx_gain = -12.0)

    def shutdown(self, error = 0, board = None ):
        pass

    def print_versions(self, device = None ):
        pass

    def probe_usrps(self):
        localusrps = uhd.find( "")
        cnt = 0
        for u in localusrps:
            self.usrps[cnt] = u.to_string()
            logger.info(f"USRP {cnt} is {self.usrps[cnt]}")
            cnt = cnt + 1
    

    def configureSdr(self, type="b200", sdrconfig=None):
    
        #self.sdrconfig = sdrconfig
        if sdrconfig == None:
            self.sdrconfig = self.defaultsdrconfig
        else:
            self.sdrconfig = sdrconfig
        #self.devicename = "winslab_b210_" + str(self.componentinstancenumber) #device names are configured properly on devices
        try:
            logger.debug(f"SDR my componentinstancenumber is {self.componentinstancenumber}")
            self.devicename = self.getUsrp(self.componentinstancenumber) #self.usrps[int(self.componentinstancenumber)] #get the list of devices online (should be done once!) and match serial to componentinstancenumber
        except Exception as ex:
            self.devicename = "THERE ARE NO USRPS CONNECTED"
            logger.error(f"Runtime error while probing usrp: {ex}")

        
        self.freq = self.sdrconfig.freq
        self.bandwidth = self.sdrconfig.bandwidth
        self.chan = self.sdrconfig.chan
        self.hw_tx_gain = self.sdrconfig.hw_tx_gain
        self.hw_rx_gain = self.sdrconfig.hw_rx_gain
        self.tx_rate= self.bandwidth /4
        self.rx_rate= self.bandwidth /4
        logger.info(f"Configuring {self.devicename}, freq={self.freq}, bandwidth={self.bandwidth}, channel={self.chan}, hw_tx_gain={self.hw_tx_gain}, hw_rx_gain={self.hw_rx_gain}")
        #self.usrp = uhd.usrp.MultiUSRP(f"name={self.devicename}")
        self.usrp = uhd.usrp.MultiUSRP(f"{self.devicename}")
        
        curr_hw_time = self.usrp.get_time_last_pps()     

        self.usrp.set_clock_source("internal")
        self.usrp.set_time_now(uhd.types.TimeSpec(0.0))
        #self.usrp.set_time_next_pps((curr_hw_time+1.0 ))
        self.usrp.set_time_next_pps(uhd.types.TimeSpec(0.0))
        #self.usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
        #self.usrp.set_start_time(uhd.time_spec_t(curr_hw_time+2.0 ) )

        self.usrp.set_rx_bandwidth(self.bandwidth, self.chan)
        self.usrp.set_tx_bandwidth(self.bandwidth, self.chan)
        
        self.usrp.set_rx_freq(self.freq, self.chan)
        self.usrp.set_tx_freq(self.freq, self.chan)
        
        self.usrp.set_rx_bandwidth(self.bandwidth,self.chan)
        self.usrp.set_tx_bandwidth(self.bandwidth,self.chan)
        
        self.usrp.set_rx_rate(self.tx_rate, self.chan)
        self.usrp.set_tx_rate(self.rx_rate, self.chan)
        
        self.usrp.set_rx_gain(self.hw_rx_gain, self.chan)
        self.usrp.set_tx_gain(self.hw_tx_gain, self.chan)
        
        #self.usrp.set_master_clock_rate(self.bandwidth*4)

        #self.usrp.set_rx_agc(True, self.chan)
        logger.info(f"------- USRP( {self.devicename } ) CONFIG --------------------" +
        f"===> CHANNEL= {self.chan}" +
        f"===> RX-BANDWIDTH= {self.usrp.get_rx_bandwidth(self.chan)}" +
        f"===> TX-BANDWIDTH=  {self.usrp.get_tx_bandwidth(self.chan)}" +
        f"===> RX-FREQ=  {self.usrp.get_rx_freq(self.chan)}" +
        f"===> TX-FREQ=  {self.usrp.get_tx_freq(self.chan)}" +
        f"===> RX-RATE=  {self.usrp.get_rx_rate(self.chan)}" +
        f"===> TX-RATE=  {self.usrp.get_tx_rate(self.chan)}" +
        f"===> RX-GAIN-NAMES=  {self.usrp.get_rx_gain_names(self.chan)}" +
        f"===> TX-GAIN-NAMES=  {self.usrp.get_tx_gain_names(self.chan)}" +
        f"===> RX-GAIN=  {self.usrp.get_rx_gain(self.chan)}" +
        f"===> TX-GAIN=  {self.usrp.get_tx_gain(self.chan)}" +
        f"===> USRP-INFO=  {self.usrp.get_pp_string()}" )
        

    
        stream_args = uhd.usrp.StreamArgs('fc32', 'sc16')
        stream_args.channels = [self.chan]
        
        self.rx_streamer = self.usrp.get_rx_stream(stream_args)
        self.tx_streamer = self.usrp.get_tx_stream(stream_args)
    
        self.tx_max_num_samps = self.tx_streamer.get_max_num_samps()
        self.rx_max_num_samps = self.rx_streamer.get_max_num_samps()
        print("Max samples that can be transmitted", self.tx_max_num_samps, " received ", self.rx_max_num_samps )

    def get_sdr_power(self,num_samps=1000000, chan=0):
        uhd.dsp.signals.get_usrp_power(self.rx_streamer, num_samps, chan)
        
    
    def ischannelclear_old(self, threshold=-70, pout=100):
        self.cca = True
        cca_threshold = threshold + 10*math.log10(100/pout)
        tx_rate = self.usrp.get_rx_rate(self.chan) / 1e6
        samps_per_est = math.floor(18 * tx_rate)
        #samps_per_est = 10
        power_dbfs = 0
        self.mutex.acquire(1)
        try:
            power_dbfs = uhd.dsp.signals.get_usrp_power(self.rx_streamer, num_samps=int(samps_per_est), chan=self.chan)
        except Exception as ex:
            logger.error(f"Runtime error in cca: {ex}")
        finally:
            self.mutex.release()
            self.start_sdr_rx()
        self.cca = False
        if (power_dbfs > cca_threshold ):
            return False, power_dbfs
        else:
            return True, power_dbfs



    def start_rx(self, rx_callback, framer):
        logger.debug(f"start_rx on usrp winslab_b210_{self.componentinstancenumber}")
        self.framer = framer
        self.rx_callback = rx_callback
        self.rx_rate = self.usrp.get_rx_rate()
        self.start_sdr_rx()
        t = Thread(target=self.rx_thread, args=[])
        t.daemon = True
        t.start()
        

    def start_sdr_rx(self):
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        self.rx_streamer.issue_stream_cmd(stream_cmd)
        
    def stop_sdr_rx(self):
        self.rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
    


    def rx_thread(self):
        
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = True
        stream_cmd.time_spec = uhd.types.TimeSpec(self.usrp.get_time_now().get_real_secs() + self.INIT_DELAY)
        cnt = 1
        logger.debug(f"rx_thread on usrp {self.devicename} on node {self.componentinstancenumber}")
        
        while(self.receiveenabled == True):
            cnt += 1
            self.mutex.acquire(1)
            try:
                rx_metadata = uhd.types.RXMetadata()
                recv_buffer = np.zeros( self.rx_max_num_samps, dtype=np.complex64)
                num_rx_samps = self.rx_streamer.recv(recv_buffer, rx_metadata)
                #self.rx_callback(num_rx_samps, recv_buffer)
                #Let's put the frame to Framehandler's queue for speed up
                if num_rx_samps > 0:
                    frm = PhyFrame(num_rx_samps, recv_buffer)
                    self.framer.frame_in_queue.put(Event(None, PhyEventTypes.RECV, frm))
                if cnt % 10 == 0:
                    cnt = 0
                    if num_rx_samps > self.samps_per_est:
                        self.computeRSSI( self.samps_per_est, recv_buffer[:self.samps_per_est],type="fc32")
                #if rx_metadata.error_code == uhd.types.RXMetadataErrorCode.overflow:
                #    print("Overflow")
                #if rx_metadata.error_code == uhd.types.RXMetadataErrorCode.late:
                #    print("Late")
                    #logger.warning("Receiver error: %s, restarting streaming...", metadata.strerror())
                    #stream_cmd.time_spec = uhd.types.TimeSpec(self.usrp.get_time_now().get_real_secs() + self.INIT_DELAY)
                    #stream_cmd.stream_now = True
                #
                if rx_metadata.error_code != 0:
                    self.rx_streamer.issue_stream_cmd(stream_cmd)
                #    print(rx_metadata.error_code)
                
            except RuntimeError as ex:
                logger.error(f"Runtime error in receive: {ex}")
            finally:
                self.mutex.release()
                pass
        logger.debug("Will not read samples from the channel any more...")           
        
    def finalize_transmit_samples(self):   
        tx_metadata = uhd.types.TXMetadata() 
        tx_metadata.end_of_burst = True
        tx_metadata.start_of_burst = False
        tx_metadata.has_time_spec = False
        num_tx_samps = self.tx_streamer.send(np.zeros((1, 0), dtype=np.complex64), tx_metadata)
        return num_tx_samps
        
    def transmit_samples(self, transmit_buffer):
        tx_metadata = uhd.types.TXMetadata()
        tx_metadata.has_time_spec = False
        #tx_metadata.time_spec = uhd.types.TimeSpec(self.usrp.get_time_now().get_real_secs() + self.INIT_DELAY)
        tx_metadata.start_of_burst = False
        tx_metadata.end_of_burst = False
        num_tx_samps = self.tx_streamer.send(transmit_buffer, tx_metadata)
        #print("TX", tx_metadata.error_code)
        return num_tx_samps