import sys
import os
import threading
import time
from bladerf              import _bladerf, _tool
from ...Generics import SDRConfiguration
from threading import Thread, Lock
from .SDRUtils import SDRUtils
import numpy as np
from ...Generics import *
from .LiquidDspUtils import *
import math

class BladeRFUtils(SDRUtils):
    
    fpgalocation = "/etc/Nuand/bladeRF/hostedx115.rbf"
    #fpgalocation = "/usr/share/Nuand/bladeRF/hostedx115.rbf"

    # bladerfs={
    #     0: "9419c6d87985ee1d13edde236573b65e",
    #     2: "5be03a9f833d94ffae498960e3d420df",
    #     1: "361ab51785f20b1ff3654438c1ddb4d6"
    # }

    bladerfs = {}

    # bladerfs={
    #     0: "c2863e4c6b8ed16e9ebe51e233da9931",
    #     1: "6f22dd084ce6d7f0ee649545f1d35a07"
    # }

    def __init__(self, componentinstancenumber) -> None:
        super().__init__(componentinstancenumber)
        self.mutex = Lock()
        self.rssi = -90
        self.bytes_per_sample = 4 # 2 int16 for complex number sc16q11
        self.receiveenabled = False
        if not bool (self.bladerfs):
            self.probe_bladerfs()

    defaultbladerfconfig = SDRConfiguration(freq =2.350e9, bandwidth = 61.44e6, chan = 0, hw_tx_gain = 30, hw_rx_gain = 0, sw_tx_gain=-12.0)


    # =============================================================================
    # Close the device and exit
    # =============================================================================
    def shutdown(self, error = 0, board = None ):
        print( "Shutting down with error code: " + str(error) )
        self.stop_sdr_rx()
        if( board != None ):
            board.close()
        #sys.exit(error)

    # =============================================================================
    # Version information
    # =============================================================================
    def print_versions(self, device = None ):
        print( "libbladeRF version: " + str(_bladerf.version()) )
        if( device != None ):
            try:
                print( "Firmware version: " + str(device.get_fw_version()) )
            except:
                print( "Firmware version: " + "ERROR" )
                raise

            try:
                print( "FPGA version: "     + str(device.get_fpga_version()) )
            except:
                print( "FPGA version: "     + "ERROR" )
                raise

        return 0
    # =============================================================================
    # Search for a bladeRF device attached to the host system
    # Returns a bladeRF device handle.
    # =============================================================================
    def probe_specific_bladerf(self, serial):
        device = None
        print( "Searching for bladeRF devices..." )
        try:
            devinfos = _bladerf.get_device_list()
            print(devinfos)
            for devinfo in devinfos:
                if devinfo.serial == serial:
                    device = "{backend}:device={usb_bus}:{usb_addr}".format(**devinfo._asdict())
                    print(devinfo.serial)
                    return device

        except _bladerf.BladeRFError:
            print( "No bladeRF devices found." )
            pass

        return device

    # =============================================================================
    # Search for a bladeRF device attached to the host system
    # Returns a bladeRF device handle.
    # =============================================================================
    def probe_bladerfs(self):
        device = None
        print( "Searching for bladeRF devices..." )
        try:
            devinfos = _bladerf.get_device_list()
            print(devinfos)
            cnt = 0;
            for devinfo in devinfos:
                self.bladerfs[cnt] = devinfo.serial
                print("Bladerf ", cnt, " has serial ", self.bladerfs[cnt])
                cnt = cnt + 1
                #if devinfo.serial == serial:
                #    device = "{backend}:device={usb_bus}:{usb_addr}".format(**devinfo._asdict())
                #    print(devinfo.serial)
                #    return device

        except _bladerf.BladeRFError:
            print( "No bladeRF devices found." )
            pass

        return device

    # =============================================================================
    # Load FPGA
    # =============================================================================
    def load_fpga(self, device, image ):

        image = os.path.abspath( image )

        if( not os.path.exists(image) ):
            print( "FPGA image does not exist: " + str(image) )
            return -1

        try:
            print( "Loading FPGA image: " + str(image ) )
            device.load_fpga( image )
            fpga_loaded  = device.is_fpga_configured()
            fpga_version = device.get_fpga_version()

            if( fpga_loaded ):
                print( "FPGA successfully loaded. Version: " + str(fpga_version) )

        except _bladerf.BladeRFError:
            print( "Error loading FPGA." )
            raise

        return 0

    # =============================================================================
    # CONFIGURE TRANSMIT CHANNEL
    # =============================================================================
    def configure_tx_channel(self):

        if( self.bladerfdevice == None ):
            print( "TX: Invalid device handle." )
            return -1

        if( self.tx_ch == None ):
            print( "TX: Invalid channel." )
            return -1

        # Configure bladeRF
        
       
        if self.componentinstancenumber == 0:
            deltafreq = 1000000
        else:
            deltafreq = 0
        self.bladerfdevice_tx_ch.frequency   = self.tx_freq #+ deltafreq
        self.bladerfdevice_tx_ch.sample_rate = self.bandwidth #40000000 #self.tx_rate
        self.bladerfdevice_tx_ch.gain        = self.tx_gain
        self.bladerfdevice_tx_ch.bandwidth   = self.bandwidth
        #self.bladerfdevice_tx_ch.gain_mode   = _bladerf.GainMode.Manual
        #self.bladerfdevice.set_gain_mode ( self.bladerfdevice_tx_ch , _bladerf.GainMode.Manual)
        # Setup stream
        self.bladerfdevice.sync_config(layout=_bladerf.ChannelLayout.TX_X1,
                        fmt=_bladerf.Format.SC16_Q11,
                        num_buffers=16,
                        buffer_size=8192*2,
                        num_transfers=8,
                        stream_timeout=500)

        # Enable module
        print( "TX: Start" )
        self.bladerfdevice_tx_ch.enable = True
        return 0


    # =============================================================================
    # CONFIGURE RECEIVE
    # =============================================================================
    def configure_rx_channel(self):

        if( self.bladerfdevice == None ):
            print( "RX: Invalid device handle." )
            return -1

        if( self.rx_ch == None ):
            print( "RX: Invalid channel." )
            return -1

        # Configure BladeRF
        

        if self.componentinstancenumber == 0:
            deltafreq = 0
        else:
            deltafreq = 1000000
        self.bladerfdevice_rx_ch.frequency   = self.rx_freq #+ deltafreq
        self.bladerfdevice_rx_ch.sample_rate = self.bandwidth #40000000 #self.rx_rate
        self.bladerfdevice_rx_ch.gain        = self.rx_gain
        self.bladerfdevice_rx_ch.bandwidth   = self.bandwidth
        #self.bladerfdevice_rx_ch.gain_mode   = _bladerf.GainMode.Manual
        #self.bladerfdevice.set_gain_mode ( self.bladerfdevice_rx_ch , _bladerf.GainMode.Manual)
        # Setup synchronous stream
        self.bladerfdevice.sync_config(layout         = _bladerf.ChannelLayout.RX_X1,
                        fmt            = _bladerf.Format.SC16_Q11,
                        num_buffers    = 16,
                        buffer_size    = 8192*2,
                        num_transfers  = 8,
                        stream_timeout = 500)

        # Enable module
        
        #self.bladerfdevice_rx_ch .enable = True
        #self.start_sdr_rx()


    def ischannelclear(self, threshold=-70, pout=100):
        if self.rssi < threshold:
            return True, self.rssi #TODO: TO BE IMPLEMENTED
        else:
            return False, self.rssi

    def configureSdr(self, type="x115", sdrconfig=defaultbladerfconfig):
        try:
            print("SDR my componentinstancenumber is ", self.componentinstancenumber)
            self.devicename = self.bladerfs[self.componentinstancenumber] #get the list of devices online (should be done once!) and match serial to componentinstancenumber
        except Exception as ex:
            self.devicename = "none"
            print("While probing bladerfs ", ex)
        print("WILL CONFIGURE BLADERF with serial ", self.devicename, " for sdr devices ", self.componentinstancenumber)
        self.sdrconfig = sdrconfig

#        self.bladerfdevice_identifier = self.probe_specific_bladerf(bytes(self.devicename,'utf-8')) #devicename is the serial of bladerf
        self.bladerfdevice_identifier = self.probe_specific_bladerf(self.devicename) #devicename is the serial of bladerf
        print(self.bladerfdevice_identifier)
        if( self.bladerfdevice_identifier == None ):
            print( "No bladeRFs detected. Exiting." )
            self.shutdown( error = -1, board = None )


        self.bladerfdevice          = _bladerf.BladeRF( self.bladerfdevice_identifier )
        self.board_name = self.bladerfdevice.board_name
        self.fpga_size  = self.bladerfdevice.fpga_size


        print( "Loading FPGA on ",self.devicename, "at ", self.fpgalocation )
        try:
            status = self.load_fpga( self.bladerfdevice, self.fpgalocation )
        except:
            print( "ERROR loading FPGA for Serial ", self.devicename, " fpga at ", self.fpgalocation  )
            raise

        if( status < 0 ):
            print( "ERROR loading FPGA." )
            self.shutdown( error = status, board = self.bladerfdevice )


        status = self.print_versions( device = self.bladerfdevice )

        tx_chan = int(self.sdrconfig.chan)
        rx_chan = int(self.sdrconfig.chan)
        self.tx_ch = _bladerf.CHANNEL_TX(tx_chan)
        self.rx_ch = _bladerf.CHANNEL_RX(rx_chan)
        print(self.tx_ch, self.rx_ch)
        self.rx_freq = int(self.sdrconfig.freq)
        self.tx_freq = int(self.sdrconfig.freq)
        self.rx_rate = int(self.sdrconfig.bandwidth)
        self.tx_rate = int(self.sdrconfig.bandwidth)
        self.tx_gain = int(self.sdrconfig.hw_tx_gain)
        self.rx_gain = int(self.sdrconfig.hw_rx_gain)
        self.bandwidth = self.sdrconfig.bandwidth

        self.bladerfdevice_rx_ch             = self.bladerfdevice.Channel(self.rx_ch)
        self.bladerfdevice_tx_ch              = self.bladerfdevice.Channel(self.tx_ch)
        #self.bladerfdevice.set_gain_mode(tx_chan, _bladerf.GainMode.FastAttack_AGC)
        #self.bladerfdevice.set_gain_mode(rx_chan, _bladerf.GainMode.FastAttack_AGC)

        
        
        #TODO FOR TESTING
        #lb = _bladerf.Loopback.BB_TXVGA1_RXLPF
        #self.bladerfdevice.loopback = _bladerf.Loopback.BB_TXVGA1_RXLPF
        #status  = self.bladerfdevice.set_loopback(lb)
        #if status < 0:
        #    print("Cannot do loopback")
        #else:
        #    print("Set loopback to ", lb)
        
        self.configure_rx_channel()
        self.configure_tx_channel()

        print("----> BLADERF(", self.bladerfdevice.get_serial(), ") CONFIG --------")
        print("----> ", self.bladerfdevice.devinfo)
        print("----> TX_CHAN", self.tx_ch)
        _tool._print_channel_details(self.bladerfdevice_tx_ch,0)
        print("----> RX_CHAN", self.rx_ch)
        _tool._print_channel_details(self.bladerfdevice_rx_ch,0)
        print("----> TX_FREQ", self.bladerfdevice.get_frequency(self.tx_ch))
        print("----> RX_FREQ", self.bladerfdevice.get_frequency(self.rx_ch))
        print("----> TX_BANDWIDTH", self.bladerfdevice.get_bandwidth(self.tx_ch))
        print("----> RX_BANDWIDTH", self.bladerfdevice.get_bandwidth(self.rx_ch))
        print("----> TX_SAMPLING_RATE", self.bladerfdevice.get_sample_rate(self.tx_ch))
        print("----> RX_SAMPLING_RATE", self.bladerfdevice.get_sample_rate(self.rx_ch))
        print("----> TX_GAIN", self.bladerfdevice.get_gain(self.tx_ch))
        print("----> RX_GAIN", self.bladerfdevice.get_gain(self.rx_ch))
#        self.configure_rx_channel()


    def start_sdr_rx(self):
        #print(f"start_usrp_rx on usrp winslab_b210_{self.componentinstancenumber}")
        self.bladerfdevice_rx_ch.enable = True
        self.receiveenabled = True
        #print( "RX: Start" )
        
    def stop_sdr_rx(self):
        self.bladerfdevice_rx_ch.enable = False
        self.receiveenabled = False
        #print( "RX: Stop" )

      
    def start_rx(self, rx_callback, framer):
        print(f"start_rx on bladerf {self.devicename}")
        self.framer = framer
        self.rx_callback = rx_callback
        t = Thread(target=self.rx_thread, args=[])
        t.daemon = True
        t.start()
        self.start_sdr_rx()
    
    def computeRSSI(self, num_samples, buffer):
        g:float = 0
        for i in range(num_samples):
            val:float = math.fabs(buffer[i])
            g += val * val
            #print("Val ", val, g)

        g = g / num_samples
        self.rssi = 10 * math.log10(math.sqrt(g)/(2048.0*1000) )
        #print("CHANNEL RSSI = ", g, self.rssi)
        

    def rx_thread(self):
        #print(f"rx_thread on bladerf{self.devicename}-->{self.componentinstancenumber}")
        #print(f"max_samps_per_packet={max_samps_per_packet}")
        
        num_samples = 1024
        buf = bytearray(num_samples*self.bytes_per_sample)
        #print(f"recv_buffer={recv_buffer")
        #buf2 = np.zeros(num_samples*2, dtype=np.int16) # sc16q1 samples
        num_samples_read = 0
        while(self.receiveenabled == True):
            #self.mutex.acquire(1)
            #print(f"rx_thread on usrp bladerf_{self.componentinstancenumber} ---> {self.devicename}", self.rssi)
            try:
                self.bladerfdevice.sync_rx(buf, num_samples)
                
                #mybuf = np.frombuffer(buf, dtype=np.int16)
                #mybuf2 = np.frombuffer(buf, dtype=np.complex64)
                mybuf2 = np.frombuffer(buf, dtype=np.int16).flatten (order="C") #// int(self.sdrconfig.sw_tx_gain)
                self.rx_callback( num_samples, mybuf2)
                self.computeRSSI( num_samples, mybuf2)
                #print("myuf=", mybuf[:5]/2048.0)
                #print(self.componentinstancenumber, ": length of received samples mybuf", len(mybuf2), " num samples ", num_samples)
            except RuntimeError as ex:
                print("Runtime error in rx_thread: ", ex)
            finally:   
                #self.mutex.release()
                pass
                #print("Released mutex")
        print("Will not read samples from the channel any more...")     
    def transmit_samples(self, transmit_buffer):
        try:
            #self.mutex.acquire(1)
            #self.stop_sdr_rx()
            num = (len(transmit_buffer)//self.bytes_per_sample)*2
            #num = len(transmit_buffer)#//self.bytes_per_sample
            #print("Number of samples to transmit", num)
            self.bladerfdevice.sync_tx(transmit_buffer.flatten(order="C"), num)
            #self.bladerfdevice.sync_tx(transmit_buffer, num)
            #print("transmitted", num)
        except RuntimeError as ex:
            print("Runtime error in receive: %s", ex)
        finally:
            #self.mutex.release()
            #self.start_sdr_rx()
            pass
     