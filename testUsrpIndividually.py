import os
import sys, getopt
import time, random, math
from enum import Enum
from pickle import FALSE
sys.path.insert(0, os.getcwd())


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader,GenericMessage,SDRConfiguration, MessageDestinationIdentifiers
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters

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
        
        payload = "USRP-BMSG-" + str(self.counter) + ": " + str(self.componentinstancenumber) 
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        # time.sleep(3)
        self.send_down(evt)
        #print("Starting broadcast")
    
         
class UsrpNode(GenericModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
    
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5)
        usrpconfig = SDRConfiguration(freq =915000000.0, bandwidth = 2000000, chan = 0, hw_tx_gain = 50.0, hw_rx_gain = 20.0, sw_tx_gain = -12.0)
        

        self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, usrpconfig=usrpconfig, topology=topology)
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
    
def main(argv):
    id = 0 #default 0 if arg -i is not given
    try:
        opts, args = getopt.getopt(argv,"hi:",["id="])
    except getopt.GetoptError:
        print ("testUsrpIndividually.py -i <nodeinstancenumber>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("testUsrpIndividually.py -i <nodeinstancenumber>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            id = arg

    topo = Topology()
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels_for_docker(UsrpNode, id)
  # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    
    while(True):
        topo.nodes[0].appl.send_self(Event(topo.nodes[0], UsrpApplicationLayerEventTypes.STARTBROADCAST, None))
        time.sleep(0.2)


if __name__ == "__main__":
    main(sys.argv[1:])
