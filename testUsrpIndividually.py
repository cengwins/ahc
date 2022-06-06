import os
import sys, getopt
import time
import signal
sys.path.insert(0, os.getcwd())

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters
from adhoccomputing.Networking.ApplicationLayer.PingPongApplicationLayer import *
import logging

         
class UsrpNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5, -50)
        sdrconfig = SDRConfiguration(freq =2484000000.0, bandwidth = 10000000, chan = 0, hw_tx_gain = 76, hw_rx_gain = 20, sw_tx_gain = -12.0)

        self.appl = PingPongApplicationLayer("PingPongApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, topology=topology,usrpconfig=sdrconfig, )
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
    id = 0 #default 0 if arg -i is not given
    try:
        opts, args = getopt.getopt(argv,"hi:",["id="])
    except getopt.GetoptError:
        logger.error ("testUsrpIndividually.py -i <nodeinstancenumber>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logger.error ("testUsrpIndividually.py -i <nodeinstancenumber>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            id = arg

    
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels_for_docker(UsrpNode, id)
  # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    
    while(True):
        topo.nodes[0].appl.send_self(Event(topo.nodes[0], PingPongApplicationLayerEventTypes.STARTBROADCAST, None))
        time.sleep(0.1)

    #time.sleep(5)
    #topo.exit()
    

def ctrlc_signal_handler(sig, frame):
    topo.exit()
    time.sleep(5)
    sys.exit(0)


def segfault_signal_handler(sig, frame):
    topo.exit()
    time.sleep(5)
    sys.exit(0)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, ctrlc_signal_handler)
    signal.signal(signal.SIGSEGV, segfault_signal_handler)
    main(sys.argv[1:])
