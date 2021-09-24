from Ahc import ComponentModel, singleton
from EttusUsrp.UhdUtils import AhcUhdUtils 
from EttusUsrp.LiquidDspUtils import *


@singleton
class FramerObjects():
    framerobjects = {}
    def add_framer(self, id, obj):
        self.framerobjects[id] = obj
    
    def get_framer_by_id(self, id):
        return self.framerobjects[id]
    
class FrameHandlerBase(ComponentModel):

    def __init__(self,componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        framers.add_framer(id(self), self)
        self.samps_per_est = 100
        self.chan = 0
        self.bandwidth = 250000
        self.freq = 2462000000.0
        self.lo_offset = 0
        self.rate = 4 * self.bandwidth
        self.wave_freq = 10000
        self.wave_ampl = 0.3
        self.hw_tx_gain = 70.0  # hardware tx antenna gain
        self.hw_rx_gain = 20.0  # hardware rx antenna gain
        self.sw_tx_gain = -12.0  # software gain
        self.duration = 1
        self.ahcuhd = AhcUhdUtils()
        self.ahcuhd.configureUsrp("winslab_b210_" + str(self.componentinstancenumber))        
        print("Configuring", "winslab_b210_" + str(self.componentinstancenumber))
        self.configure()

        
framers = FramerObjects()
