import sys
import os
import threading
import time
from bladerf              import _bladerf
from ...Generics import SDRConfiguration
from threading import Thread, Lock
from .SDRUtils import SDRUtils
import numpy as np

class BladeRFUtils(SDRUtils):
    
    fpgalocation = "/usr/local/share/hostedx115-latest.rbf"


    bladerfs={
        0: "9419c6d87985ee1d13edde236573b65e",
        2: "5be03a9f833d94ffae498960e3d420df",
        1: "361ab51785f20b1ff3654438c1ddb4d6"
    }


    def __init__(self, componentinstancenumber) -> None:
        super().__init__(componentinstancenumber)
        self.mutex = Lock()
        self.cca = False
        self.bytes_per_sample = 4 # 2 int16 for complex number sc16q11

    defaultbladerfconfig = SDRConfiguration(freq =2.350e9, bandwidth = 61.44e6, chan = 0, hw_tx_gain = 30, hw_rx_gain = 0, sw_tx_gain=-12.0)


    # =============================================================================
    # Close the device and exit
    # =============================================================================
    def shutdown(self, error = 0, board = None ):
        print( "Shutting down with error code: " + str(error) )
        if( board != None ):
            board.close()
        sys.exit(error)

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
                print(type(devinfo.serial))
                if devinfo.serial == serial:
                    device = "{backend}:device={usb_bus}:{usb_addr}".format(**devinfo._asdict())
                    print(devinfo.serial)
                    return device

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

        if( self.tx_chan == None ):
            print( "TX: Invalid channel." )
            return -1

        # Configure bladeRF
        self.bladerfdevice_tx_ch              = self.bladerfdevice.Channel(self.tx_chan)
        self.bladerfdevice_tx_ch.frequency   = self.tx_freq
        self.bladerfdevice_tx_ch.sample_rate = self.tx_rate
        self.bladerfdevice_tx_ch.gain        = self.tx_gain

        # Setup stream
        self.bladerfdevice.sync_config(layout=_bladerf.ChannelLayout.TX_X1,
                        fmt=_bladerf.Format.SC16_Q11,
                        num_buffers=16,
                        buffer_size=8192,
                        num_transfers=8,
                        stream_timeout=3500)

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

        if( self.rx_chan == None ):
            print( "RX: Invalid channel." )
            return -1

        # Configure BladeRF
        self.bladerfdevice_rx_ch             = self.bladerfdevice.Channel(self.rx_chan)
        self.bladerfdevice_rx_ch.frequency   = self.rx_freq
        self.bladerfdevice_rx_ch.sample_rate = self.rx_rate
        self.bladerfdevice_rx_ch.gain        = self.rx_gain

        # Setup synchronous stream
        self.bladerfdevice.sync_config(layout         = _bladerf.ChannelLayout.RX_X1,
                        fmt            = _bladerf.Format.SC16_Q11,
                        num_buffers    = 16,
                        buffer_size    = 8192,
                        num_transfers  = 8,
                        stream_timeout = 3500)

        # Enable module
        
        #self.bladerfdevice_rx_ch .enable = True
        #self.start_sdr_rx()


    def ischannelclear(self, threshold=-70, pout=100):
        return True, 0 #TODO: TO BE IMPLEMENTED

    def configureSdr(self, type="x115", sdrconfig=defaultbladerfconfig):
        self.devicename = self.bladerfs[self.componentinstancenumber] #get the list of devices online (should be done once!) and match serial to componentinstancenumber
        self.sdrconfig = sdrconfig

        self.bladerfdevice_identifier = self.probe_specific_bladerf(bytes(self.devicename,'utf-8')) #devicename is the serial of bladerf
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

        self.tx_chan = int(self.sdrconfig.chan)
        self.rx_chan = int(self.sdrconfig.chan)
        self.tx_ch = _bladerf.CHANNEL_TX(self.tx_chan)
        self.rx_ch = _bladerf.CHANNEL_TX(self.rx_chan)
        print(self.tx_ch, self.rx_ch)
        self.rx_freq = self.tx_freq = int(self.sdrconfig.freq)
        self.rx_rate = self.tx_rate = int(self.sdrconfig.bandwidth)
        self.tx_gain = int(self.sdrconfig.hw_tx_gain)
        self.rx_gain = int(self.sdrconfig.hw_rx_gain)


        self.configure_rx_channel()

        self.configure_tx_channel()

        print("------- BLADERF(", self.bladerfdevice.get_serial(), ") CONFIG --------")
        print("----> ", self.bladerfdevice.devinfo)
        print("----> TX_CHAN", self.tx_chan)
        print("----> RX_CHAN", self.rx_chan)
        print("----> TX_FREQ", self.bladerfdevice.get_frequency(self.tx_chan))
        print("----> RX_FREQ", self.bladerfdevice.get_frequency(self.rx_chan))
        print("----> TX_BANDWIDTH", self.bladerfdevice.get_bandwidth(self.tx_chan))
        print("----> RX_BANDWIDTH", self.bladerfdevice.get_bandwidth(self.rx_chan))
        print("----> TX_SAMPLING_RATE", self.bladerfdevice.get_sample_rate(self.tx_chan))
        print("----> RX_SAMPLING_RATE", self.bladerfdevice.get_sample_rate(self.rx_chan))
        print("----> TX_GAIN", self.bladerfdevice.get_gain(self.tx_chan))
        print("----> RX_GAIN", self.bladerfdevice.get_gain(self.rx_chan))
#        self.configure_rx_channel()


    def start_sdr_rx(self):
        #print(f"start_usrp_rx on usrp winslab_b210_{self.componentinstancenumber}")
        self.bladerfdevice_rx_ch.enable = True
        #print( "RX: Start" )
        
    def stop_sdr_rx(self):
        self.bladerfdevice_rx_ch.enable = False
        #print( "RX: Stop" )

      
    def start_rx(self, rx_callback, framer):
        print(f"start_rx on bladerf {self.devicename}")
        self.framer = framer
        self.rx_callback = rx_callback
        t = Thread(target=self.rx_thread, args=[])
        t.daemon = True
        t.start()
        self.start_sdr_rx()
     
    def rx_thread(self):
        print(f"rx_thread on bladerf{self.devicename}-->{self.componentinstancenumber}")
        #print(f"max_samps_per_packet={max_samps_per_packet}")
        
        num_samples = 256
        buf = bytearray(num_samples*self.bytes_per_sample)
        #print(f"recv_buffer={recv_buffer")
        
        while(True):
            self.cca = False #TODO
            if self.cca == False:
                self.mutex.acquire(1)
                #print(f"rx_thread on usrp bladerf_{self.componentinstancenumber} ---> {self.devicename}")
                try:
                    self.bladerfdevice.sync_rx(buf, num_samples)
                    mybuf = np.frombuffer(buf, dtype=np.int16)
                    self.rx_callback( num_samples, mybuf)
                    #print("Length of received samples mybuf", len(mybuf), " num samples ", num_samples)
                except RuntimeError as ex:
                    print("Runtime error in receive: %s", ex)
                finally:
                    self.mutex.release()
                    #print("Released mutex")
                
    def transmit_samples(self, transmit_buffer):
        try:
            #self.mutex.acquire(1)
            #self.stop_sdr_rx()
            bytes_per_sample = 4
            #num = len(transmit_buffer)//bytes_per_sample
            num = len(transmit_buffer)//self.bytes_per_sample
            #print("Number of samples to transmit", num)
            self.bladerfdevice.sync_tx(transmit_buffer, num)
            #print("transmitted", num)
        except RuntimeError as ex:
            print("Runtime error in receive: %s", ex)
        finally:
            #self.mutex.release()
            self.start_sdr_rx()

    def float_to_sc16q11(indata, outdata, n):
        pass

    def  sc16q11_to_float(indata, outdata,n):
        pass