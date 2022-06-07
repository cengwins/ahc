import os
import sys, getopt
import time
import signal
sys.path.insert(0, os.getcwd())

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.BladeRFOfdmFlexFramePhy import  BladeRFOfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters
from adhoccomputing.Networking.ApplicationLayer.PingPongApplicationLayer import *
import logging


class BladeRFNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
        
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn)
        # SUBCOMPONENTS
        
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5, -40)
        sdrconfig = SDRConfiguration(freq =2484000000, bandwidth = 1500000, chan = 0, hw_tx_gain = 30, hw_rx_gain = 39, sw_tx_gain = -12.0)
       

        self.appl = PingPongApplicationLayer("PingPongApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = BladeRFOfdmFlexFramePhy("BladeRFOfdmFlexFramePhy", componentinstancenumber, usrpconfig=sdrconfig, topology=topology)
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber,  configurationparameters=macconfig, sdr=self.phy.sdrdev, topology=topology)
        
        self.components.append(self.appl)
        self.components.append(self.phy)
        self.components.append(self.mac)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appl.connect_me_to_component(ConnectorTypes.UP, self) #Not required if nodemodel will do nothing
        self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.mac)
        
        self.mac.connect_me_to_component(ConnectorTypes.UP, self.appl)
        self.mac.connect_me_to_component(ConnectorTypes.DOWN, self.phy)
        
        # Connect the bottom component to the composite component....
        self.phy.connect_me_to_component(ConnectorTypes.UP, self.mac)
        self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        
        # self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        # self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)
    
        
topo = Topology()
def main(argv):

    setAHCLogLevel(logging.INFO)
    num_nodes = 1
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels(num_nodes, BladeRFNode)
    #topo.mp_construct_sdr_topology_without_channels(num_nodes, BladeRFNode)
  #topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    time.sleep(1)
    i = 1
    while(i<10000):
        topo.nodes[0].appl.send_self(Event(topo.nodes[0], PingPongApplicationLayerEventTypes.STARTBROADCAST, "BMSG-"))
        i += 1
        time.sleep(0.1)

    
    time.sleep(3)
    topo.exit()
    
    

def ctrlc_signal_handler(sig, frame):
    topo.exit()
    time.sleep(1)
    sys.exit(0)


def segfault_signal_handler(sig, frame):
    topo.exit()
    time.sleep(5)
    sys.exit(0)

if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, ctrlc_signal_handler)
    signal.signal(signal.SIGSEGV, segfault_signal_handler)
    main(sys.argv[1:])
