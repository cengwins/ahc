from ...Generics import SDRConfiguration

class SDRUtils():

    defaultsdrconfig = SDRConfiguration(freq =2162000000.0, bandwidth = 1000000, chan = 0, hw_tx_gain = 50.0, hw_rx_gain = 20.0, sw_tx_gain=-12.0)

    def __init__(self, componentinstancenumber) -> None:
        self.componentinstancenumber = componentinstancenumber
        pass

    def configureSdr(self, type="b200", sdrconfig=defaultsdrconfig):
        print("Not implemented configureSdr, ", type)

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

    def finalize_transmit_samples(self):
        pass