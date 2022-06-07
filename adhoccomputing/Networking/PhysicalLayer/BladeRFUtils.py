import sys
import os
import threading
import time
from bladerf              import _bladerf, _tool
from bladerf._bladerf import libbladeRF
from ...Generics import *
from threading import Thread, Lock
from .SDRUtils import SDRUtils
import numpy as np
from ...Generics import *
from .LiquidDspUtils import *
import math
from ...Networking.PhysicalLayer.FrameHandlerBase import PhyEventTypes, PhyFrame

class BladeRFUtils(SDRUtils):
    
    fpgalocation = "/etc/Nuand/bladeRF/hostedx115.rbf"
    #fpgalocation = "/usr/share/Nuand/bladeRF/hostedx115.rbf"

    # bladerfs={
    #     0: "9419c6d87985ee1d13edde236573b65e",
    #     2: "5be03a9f833d94ffae498960e3d420df",
    #     1: "361ab51785f20b1ff3654438c1ddb4d6"
    # }


    # bladerfs={
    #     0: "c2863e4c6b8ed16e9ebe51e233da9931",
    #     1: "6f22dd084ce6d7f0ee649545f1d35a07"
    # }

    def __init__(self, componentinstancenumber) -> None:
        super().__init__(componentinstancenumber)
        self.mutex = Lock()
        
        self.bytes_per_sample = 4 # 2 int16 for complex number sc16q11
        self.receiveenabled = False
        if not bool (self.bladerfs):
            self.probe_bladerfs()

    #defaultbladerfconfig = SDRConfiguration(freq =2.350e9, bandwidth = 61.44e6, chan = 0, hw_tx_gain = 30, hw_rx_gain = 0, sw_tx_gain=-12.0)


    # =============================================================================
    # Close the device and exit
    # =============================================================================
    def shutdown(self, error = 0, board = None ):
        logger.debug(f"Shutting down with error code: {str(error)}" )
        self.stop_sdr_rx()
        if( board != None ):
            board.close()
        #sys.exit(error)

    # =============================================================================
    # Version information
    # =============================================================================
    def print_versions(self, device = None ):
        logger.debug(f"libbladeRF version: {str(_bladerf.version())}" )
        if( device != None ):
            try:
                logger.debug(f"Firmware version: {str(device.get_fw_version())}" )
                pass
            except:
                logger.critical( "Firmware version: ERROR" )
                raise

            try:
                logger.debug(f"FPGA version: {str(device.get_fpga_version())}" )
            except:
                logger.critical( "FPGA version: ERROR" )
                raise

        return 0
    # =============================================================================
    # Search for a bladeRF device attached to the host system
    # Returns a bladeRF device handle.
    # =============================================================================
    def probe_specific_bladerf(self, serial):
        device = None
        logger.debug( "Searching for bladeRF devices..." )
        try:
            devinfos = _bladerf.get_device_list()
            for devinfo in devinfos:
                if devinfo.serial == serial:
                    device = "{backend}:device={usb_bus}:{usb_addr}".format(**devinfo._asdict())
                    return device

        except _bladerf.BladeRFError:
            logger.critical( "No bladeRF devices found." )
            pass

        return device

    # =============================================================================
    # Search for a bladeRF device attached to the host system
    # Returns a bladeRF device handle.
    # =============================================================================
    def probe_bladerfs(self):
        device = None
        logger.debug( "Searching for bladeRF devices..." )
        try:
            devinfos = _bladerf.get_device_list()
            cnt = 0;
            for devinfo in devinfos:
                self.bladerfs[cnt] = devinfo.serial
                logger.debug(f"Bladerf {cnt} has serial {self.bladerfs[cnt]}" )
                cnt = cnt + 1
                #if devinfo.serial == serial:
                #    device = "{backend}:device={usb_bus}:{usb_addr}".format(**devinfo._asdict())
                #    return device

        except _bladerf.BladeRFError:
            logger.critical( "No bladeRF devices found." )
            pass

        return device

    # =============================================================================
    # Load FPGA
    # =============================================================================
    def load_fpga(self, device, image ):

        image = os.path.abspath( image )

        if( not os.path.exists(image) ):
            logger.critical(f"FPGA image does not exist: {str(image)}" )
            return -1

        try:
            logger.debug(f"Loading FPGA image:  {str(image )}" )
            device.load_fpga( image )
            fpga_loaded  = device.is_fpga_configured()
            fpga_version = device.get_fpga_version()

            if( fpga_loaded ):
                logger.debug(f"FPGA successfully loaded. Version: {str(fpga_version)}" )

        except _bladerf.BladeRFError:
            logger.critical(f"Error loading FPGA image:  {str(image )}" )

        return 0

    # =============================================================================
    # CONFIGURE TRANSMIT CHANNEL
    # =============================================================================
    def configure_tx_channel(self):

        if( self.bladerfdevice == None ):
            logger.debug( "TX: Invalid device handle." )
            return -1

        if( self.tx_ch == None ):
            logger.debug( "TX: Invalid channel." )
            return -1

        # Configure bladeRF

        
        self.bladerfdevice_tx_ch.frequency   = self.tx_freq #+ deltafreq
        self.bladerfdevice_tx_ch.sample_rate = self.tx_rate
        #self.bladerfdevice_tx_ch.bandwidth   = self.bandwidth
        #self.bladerfdevice_tx_ch.gain        = self.tx_gain
        
        #self.bladerfdevice_tx_ch.gain_mode   = _bladerf.GainMode.Manual
        #self.bladerfdevice.set_gain_mode ( self.bladerfdevice_tx_ch , _bladerf.GainMode.Manual)
        # Setup stream
        self.bladerfdevice.sync_config(layout=_bladerf.ChannelLayout.TX_X1,
                        fmt=_bladerf.Format.SC16_Q11,
                        num_buffers    = 256,
                        buffer_size    = 8192,
                        num_transfers  = 32,
                        stream_timeout=100)

        # Enable module
        logger.debug( "TX: Start" )
        self.bladerfdevice_tx_ch.enable = True
        return 0


    # =============================================================================
    # CONFIGURE RECEIVE
    # =============================================================================
    def configure_rx_channel(self):

        if( self.bladerfdevice == None ):
            logger.debug( "RX: Invalid device handle." )
            return -1

        if( self.rx_ch == None ):
            logger.debug( "RX: Invalid channel." )
            return -1

        # Configure BladeRF
        
        #self.bladerfdevice_rx_ch .enable = True
        self.bladerfdevice_rx_ch.frequency   = self.rx_freq #+ deltafreq
        self.bladerfdevice_rx_ch.sample_rate = self.rx_rate
        #self.bladerfdevice_rx_ch.bandwidth   = self.bandwidth   # Will set later down
        #self.bladerfdevice_rx_ch.gain        = self.rx_gain
        self.bladerfdevice_rx_ch.gain_mode   = _bladerf.GainMode.Manual
        #self.bladerfdevice.set_gain_mode ( self.bladerfdevice_rx_ch , _bladerf.GainMode.Manual)
        # Setup synchronous stream
        self.bladerfdevice.sync_config(layout         = _bladerf.ChannelLayout.RX_X1,
                        fmt            = _bladerf.Format.SC16_Q11,
                        num_buffers    = 256,
                        buffer_size    = 8192,
                        num_transfers  = 32,
                        stream_timeout = 100)

        # Enable module
        
        #self.bladerfdevice_rx_ch .enable = True
        #self.start_sdr_rx()



    def configureSdr(self, type="x115", sdrconfig=None):
        try:
            #self.devicename = self.bladerfs[self.componentinstancenumber] #get the list of devices online (should be done once!) and match serial to componentinstancenumber
            self.devicename = self.getBladeRF (self.componentinstancenumber) #get the list of devices online (should be done once!) and match serial to componentinstancenumber
        except Exception as ex:
            self.devicename = "none"
            logger.critical(f"Error while probing bladerfs {ex}")
        logger.info(f"WILL CONFIGURE BLADERF with serial {self.devicename} for sdr devices {self.componentinstancenumber}")
        if sdrconfig == None:
            self.sdrconfig = self.defaultsdrconfig
        else:
            self.sdrconfig = sdrconfig

#        self.bladerfdevice_identifier = self.probe_specific_bladerf(bytes(self.devicename,'utf-8')) #devicename is the serial of bladerf
        self.bladerfdevice_identifier = self.probe_specific_bladerf(self.devicename) #devicename is the serial of bladerf
        logger.debug(str(self.bladerfdevice_identifier))
        if( self.bladerfdevice_identifier == None ):
            logger.error( "No bladeRFs detected. Exiting." )
            self.shutdown( error = -1, board = None )


        self.bladerfdevice          = _bladerf.BladeRF( self.bladerfdevice_identifier )
        self.board_name = self.bladerfdevice.board_name
        self.fpga_size  = self.bladerfdevice.fpga_size

        #self.bladerfdevice.device_reset()
        #self.bladerfdevice.set_tuning_mode(1)
        

        logger.debug(f"Loading FPGA on {self.devicename} at {self.fpgalocation}" )
        try:
            status = self.load_fpga( self.bladerfdevice, self.fpgalocation )
        except:
            logger.critical( "ERROR loading FPGA for Serial {self.devicename} fpga at {self.fpgalocation}")
            raise

        if( status < 0 ):
            logger.critical( "ERROR loading FPGA." )
            self.shutdown( error = status, board = self.bladerfdevice )


        status = self.print_versions( device = self.bladerfdevice )

        tx_chan = int(self.sdrconfig.chan)
        rx_chan = int(self.sdrconfig.chan)
        self.tx_ch = _bladerf.CHANNEL_TX(tx_chan)
        self.rx_ch = _bladerf.CHANNEL_RX(rx_chan)
        self.rx_freq = int(self.sdrconfig.freq)
        self.tx_freq = int(self.sdrconfig.freq)
        self.rx_rate = int(self.sdrconfig.bandwidth) * 1
        self.tx_rate = int(self.sdrconfig.bandwidth) * 1
        self.tx_gain = int(self.sdrconfig.hw_tx_gain)
        self.rx_gain = int(self.sdrconfig.hw_rx_gain)
        self.bandwidth = self.sdrconfig.bandwidth
        
        #self.bladerfdevice.set_frequency(0, self.rx_freq)
        
        self.bladerfdevice_rx_ch             = self.bladerfdevice.Channel(self.rx_ch)
        self.bladerfdevice_tx_ch              = self.bladerfdevice.Channel(self.tx_ch)
        #self.bladerfdevice.set_gain_mode(tx_chan, _bladerf.GainMode.FastAttack_AGC)
        #self.bladerfdevice.set_gain_mode(rx_chan, _bladerf.GainMode.FastAttack_AGC)
  
        
        #TODO FOR TESTING
        #lb = _bladerf.Loopback.BB_TXVGA1_RXLPF
        #self.bladerfdevice.loopback = _bladerf.Loopback.BB_TXVGA1_RXLPF
        #status  = self.bladerfdevice.set_loopback(lb)
        #if status < 0:
        #    logger.debug("Cannot do loopback")
        #else:
        #    logger.debug(f"Set loopback to {lb}"")
        
        self.configure_rx_channel()
        self.configure_tx_channel()
        
        #timestamp: libbladeRF.bladerf_timestamp = 0
        #bqt = _bladerf.ffi.new("struct bladerf_quick_tune *")
        #libbladeRF.bladerf_schedule_retune(self.bladerfdevice.dev[0], 0, timestamp, int(self.rx_freq), bqt)
        #print(bqt.freqsel, bqt.vcocap, bqt.nint, bqt.nfrac, bqt.flags)
        #libbladeRF.bladerf_schedule_retune(self.bladerfdevice.dev[0], 1, timestamp, int(self.rx_freq), bqt)
        #print(bqt.freqsel, bqt.vcocap, bqt.nint, bqt.nfrac, bqt.flags)
        
#         RX Gain
# Overall: 5 to 66 dB
# LNA: 0 to 6 dB (step of 3 dB)
# VGA1: 5 to 30 dB (step of 1 dB)
# VGA2: 0 to 30 dB (step of 1 dB)
# Stage names: lna, rxvga1, rxvga2


        libbladeRF.bladerf_log_set_verbosity(3)

        actualbandwidth = _bladerf.ffi.new("bladerf_bandwidth *")
        libbladeRF.bladerf_set_bandwidth(self.bladerfdevice.dev[0], 0,self.bandwidth, actualbandwidth)
        libbladeRF.bladerf_set_bandwidth(self.bladerfdevice.dev[0], 1,self.bandwidth, actualbandwidth)
        print("Actual bandwidth =", actualbandwidth[0])

        libbladeRF.bladerf_set_lna_gain(self.bladerfdevice.dev[0], 3)
        libbladeRF.bladerf_set_rxvga1(self.bladerfdevice.dev[0], 20)
        libbladeRF.bladerf_set_rxvga2(self.bladerfdevice.dev[0], 10)
# TX Gain
# Overall: -35 to 21 dB
# VGA1: -35 to -4 dB (step of 1 dB)
# VGA2: 0 to 25 dB (step of 1 dB)
# Stage names: txvga1, txvga2
# Frequency: 237500000 to 3800000000 Hz
# Bandwidth: 1500000 to 28000000 Hz
# Sample Rate: 80000 to 40000000 Hz (recommended max)

        libbladeRF.bladerf_set_txvga1(self.bladerfdevice.dev[0], -4)
        libbladeRF.bladerf_set_txvga2(self.bladerfdevice.dev[0], 10)
       

        logger.info(f"\n===> BLADERF {self.bladerfdevice.get_serial()} CONFIG" + 
                f"\n===> TX_CHAN {self.tx_ch}" +
                f"\n===> RX_CHAN {self.rx_ch}" +
                f"\n===> TX_FREQ {self.bladerfdevice.get_frequency(self.tx_ch)}" +
                f"\n===> RX_FREQ {self.bladerfdevice.get_frequency(self.rx_ch)}" +
                f"\n===> TX_BANDWIDTH {self.bladerfdevice.get_bandwidth(self.tx_ch)}" +
                f"\n===> RX_BANDWIDTH {self.bladerfdevice.get_bandwidth(self.rx_ch)}"+
                f"\n===> TX_SAMPLING_RATE {self.bladerfdevice.get_sample_rate(self.tx_ch)}"+
                f"\n===> RX_SAMPLING_RATE {self.bladerfdevice.get_sample_rate(self.rx_ch)}"+
                f"\n===> TX_GAIN {self.bladerfdevice.get_gain(self.tx_ch)}" +
                f"\n===> RX_GAIN {self.bladerfdevice.get_gain(self.rx_ch)}")
#        self.configure_rx_channel()


    def start_sdr_rx(self):
        logger.debug(f"start_usrp_rx on usrp winslab_b210_{self.componentinstancenumber}")
        self.bladerfdevice_rx_ch.enable = True
        self.receiveenabled = True
        logger.debug( "RX: Start" )
        
    def stop_sdr_rx(self):
        self.bladerfdevice_rx_ch.enable = False
        self.receiveenabled = False
        logger.debug( "RX: Stop" )

      
    def start_rx(self, rx_callback, framer):
        logger.debug(f"start_rx on bladerf {self.devicename}")
        self.framer = framer
        self.rx_callback = rx_callback
        t = Thread(target=self.rx_thread, args=[])
        t.daemon = True
        t.start()
        self.start_sdr_rx()
    
        

    def rx_thread(self):
        cnt = 1
        num_samples = self.framer.fgbuffer_len
        
        num_samples_read = 0
        while(self.receiveenabled == True):
            cnt += 1
            #self.mutex.acquire(1)
            try:
                buf = bytearray(num_samples*self.bytes_per_sample)
                self.bladerfdevice.sync_rx(buf, num_samples)
                mybuf2 = np.frombuffer(buf, dtype=np.int16).flatten (order="C") #// int(self.sdrconfig.sw_tx_gain)
                #self.rx_callback( num_samples, mybuf2)
                if num_samples > 0:
                    frm = PhyFrame(num_samples, mybuf2)
                    self.framer.frame_in_queue.put(Event(None, PhyEventTypes.RECV, frm))
                #if cnt > 1:
                #    cnt = 1
                #    if num_samples*2 > self.samps_per_est:
                #        self.computeRSSI( self.samps_per_est*2, mybuf2[:self.samps_per_est*2],type="sc16")
                #logger.applog(f"Num samples {len(buf)} {num_samples} {len(mybuf2)}")
            except RuntimeError as ex:
                logger.error("Runtime error in rx_thread: {ex}")
            finally:   
                #self.mutex.release()
                pass
        logger.debug("Will not read samples from the channel any more...")     
    def transmit_samples(self, transmit_buffer):
        try:
            #self.mutex.acquire(1)
            #self.stop_sdr_rx()
            num = (len(transmit_buffer)//self.bytes_per_sample)*2
            #num = len(transmit_buffer)#//self.bytes_per_sample
           
            self.bladerfdevice.sync_tx(transmit_buffer.flatten(order="C"), num)
            #self.bladerfdevice.sync_tx(transmit_buffer, num)
        except RuntimeError as ex:
            logger.error(f"Runtime error in receive: {ex}")
        finally:
            #self.mutex.release()
            #self.start_sdr_rx()
            pass
     