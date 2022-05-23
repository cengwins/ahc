import os
import sys
import time, random, math
from enum import Enum
from pickle import FALSE
import signal

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader,GenericMessage,SDRConfiguration, MessageDestinationIdentifiers
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.BladeRFOfdmFlexFramePhy import  BladeRFOfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters

sys.path.append(os.getcwd())

# define your own message types
class ApplicationLayerMessageTypes(Enum):
    BROADCAST = "BROADCAST"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


class UsrpApplicationLayerEventTypes(Enum):
    STARTBROADCAST = "startbroadcast"


class UsrpApplicationLayer(GenericModel):
    def on_init(self, eventobj: Event):
        self.counter = 0
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers[UsrpApplicationLayerEventTypes.STARTBROADCAST] = self.on_startbroadcast

    def on_message_from_top(self, eventobj: Event):
    # print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        print(f"I am Node.{self.componentinstancenumber}, received from Node.{eventobj.eventcontent.header.messagefrom} a message: {eventobj.eventcontent.payload}")    
        evt.eventcontent.header.messageto = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload + "-" + str(self.componentinstancenumber)
        #print(f"I am {self.componentname}.{self.componentinstancenumber}, sending down eventcontent={eventobj.eventcontent.payload}\n")
        time.sleep(0.1)
        self.send_down(evt)  # PINGPONG
    
    def on_startbroadcast(self, eventobj: Event):
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.BROADCAST, self.componentinstancenumber, MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        self.counter = self.counter + 1
        
        payload = "BLADERF-BMSG-" + str(self.counter) + ": " + str(self.componentinstancenumber) 
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        #time.sleep(0.1)
        self.send_down(evt)
        #print("Starting broadcast", self.componentinstancenumber)
    
         
class BladeRFNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5, -30)
        usrpconfig = SDRConfiguration(freq =900000000.0, bandwidth = 250000, chan = 0, hw_tx_gain = 50.0, hw_rx_gain = 20.0, sw_tx_gain = -12.0)
        bladerfconfig = SDRConfiguration(freq =915000000, bandwidth = 2000000, chan = 0, hw_tx_gain = 30, hw_rx_gain = 0, sw_tx_gain = -1.0)
        
        self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = BladeRFOfdmFlexFramePhy("BladeRFOfdmFlexFramePhy", componentinstancenumber, usrpconfig=bladerfconfig, topology=topology)
        #print(self.phy.sdrdev)
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
    
        
topo = Topology()
def main():
    num_nodes = 3
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels(num_nodes, BladeRFNode)
  # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    i = 0
    while(i < 10000):
        for k in range(num_nodes):
            topo.nodes[k].appl.send_self(Event(topo.nodes[k], UsrpApplicationLayerEventTypes.STARTBROADCAST, None))
            time.sleep(0.1)
            pass
        #time.sleep(0.1)
        #topo.nodes[0].appl.send_self(Event(topo.nodes[0], UsrpApplicationLayerEventTypes.STARTBROADCAST, None))
        #time.sleep(0.1)
        i = i + 1

    time.sleep(5)
    topo.exit()
    
    

def ctrlc_signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    topo.exit()
    time.sleep(5)
    sys.exit(0)


def segfault_signal_handler(sig, frame):
    print('Segmentation Fault')
    topo.exit()
    time.sleep(5)
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, ctrlc_signal_handler)
    signal.signal(signal.SIGSEGV, segfault_signal_handler)
    main()
