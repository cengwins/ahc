import bladerf
from ...Generics import SDRConfiguration

class SDRUtils():


    bladerfs={
        0: "9419c6d87985ee1d13edde236573b65e",
        1: "5be03a9f833d94ffae498960e3d420df",
        2: "361ab51785f20b1ff3654438c1ddb4d6"
    }


    defaultsdrconfig = SDRConfiguration(freq =2162000000.0, bandwidth = 1000000, chan = 0, hw_tx_gain = 50.0, hw_rx_gain = 20.0, sw_tx_gain=-12.0)

    def __init__(self, componentinstancenumber) -> None:
        self.componentinstancenumber = componentinstancenumber
        pass

    def configureSdr(self, type="b200", sdrconfig=defaultsdrconfig):
        print("Not implemented configureSdr, ", type)
        if type=="b200":
            devicename = "winslab_b210_" + str(self.componentinstancenumber) #device names are configured properly on devices
            self.configureUsrp(devicename, type, sdrconfig)
        else:
            if type=="x115":
                devicename = self.bladerfs[self.componentinstancenumber] #get the list of devices online (should be done once!) and match serial to componentinstancenumber
                self.configureBladeRF(devicename, type, sdrconfig)

    def ischannelclear(self, threshold=-70, pout=100):
        print("Not implemented ischannelclear")
        pass

    def get_sdr_power(self,num_samps=1000000, chan=0):
        print("Not implemented get_sdr_power")
        pass

    def start_rx(self, rx_callback, framer):
        print("Not implemented start_rx")
        pass

    def start_sdr_rx(self):
        print("Not implemented start_sdr_rx")
        pass
      
    def stop_sdr_rx(self):
        print("Not implemented stop_sdr_rx")
        pass

    def rx_thread(self):
        print("Not implemented rx_thread")
        pass

    def transmit_samples(self, transmit_buffer):
        print("Not implemented transmit_samples")
        pass