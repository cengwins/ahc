import os
import sys
import time, random, math
from enum import Enum
from pickle import FALSE



from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.PhysicalLayer.BladeRFOfdmFlexFramePhy import  BladeRFOfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters
from adhoccomputing.Networking.ApplicationLayer.PingPongApplicationLayer import *
import logging
 
macconfig = MacCsmaPPersistentConfigurationParameters(0.5, -45)
bladerfconfig = SDRConfiguration(freq =2484000000,      bandwidth = 20000000,   chan = 0,   hw_tx_gain = 0,     hw_rx_gain = 39,    sw_tx_gain = -12.0)
usrpconfig =    SDRConfiguration(freq =2484000000.0,    bandwidth = 20000000,   chan = 0,   hw_tx_gain = 70,    hw_rx_gain = 20,    sw_tx_gain = -12.0)    
  
class UsrpNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        
        self.appl = PingPongApplicationLayer("PingPongApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, usrpconfig=usrpconfig, topology=topology)
        print(self.phy.sdrdev)
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber,  configurationparameters=macconfig, sdr=self.phy.sdrdev,topology=topology)
        
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
    

class BladeRFNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        i = 0
        while(True):
            #logger.applog("Will start poking")
            self.appl.send_self(Event(self, PingPongApplicationLayerEventTypes.STARTBROADCAST, None))
            time.sleep(5)    
        
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn)
        # SUBCOMPONENTS
        
        self.appl = PingPongApplicationLayer("PingPongApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = BladeRFOfdmFlexFramePhy("BladeRFOfdmFlexFramePhy", componentinstancenumber, usrpconfig=bladerfconfig, topology=topology)
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
    
      

def main():
    setAHCLogLevel(logging.INFO)
    topo = Topology()
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_usrp_bladerf(1,1, UsrpNode, BladeRFNode)
  # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    i = 0
    while(i < 10000):
        topo.nodes[0].appl.send_self(Event(topo.nodes[0], PingPongApplicationLayerEventTypes.STARTBROADCAST, None))
        time.sleep(0.1)
        #topo.nodes[1].appl.send_self(Event(topo.nodes[1], PingPongApplicationLayerEventTypes.STARTBROADCAST, None))
        #time.sleep(0.1)
        i = i + 1
    topo.exit()


if __name__ == "__main__":
    main()
