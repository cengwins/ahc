import os
import sys
import time, random, math
from enum import Enum
from pickle import FALSE
sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessage, GenericMessageHeader, FramerObjects
from Ahc import ComponentRegistry
from PhysicalLayers.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
registry = ComponentRegistry()
from Channels.Channels import FIFOBroadcastPerfectChannel
from EttusUsrp.UhdUtils import AhcUhdUtils

framers = FramerObjects()


# define your own message types
class ApplicationLayerMessageTypes(Enum):
    BROADCAST = "BROADCAST"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


class UsrpNodeEventTypes(Enum):
    STARTBROADCAST = "startbroadcast"


class UsrpApplicationLayer(ComponentModel):
    def on_init(self, eventobj: Event):
        pass
    
    def on_message_from_bottom(self, eventobj: Event):
        #print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        evt = Event(self, EventTypes.MFRB, eventobj.eventcontent)
        self.send_up(evt)
        
    def on_message_from_top(self, eventobj: Event):
        #print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        ahcuhd = framers.get_ahcuhd_by_id(self.componentinstancenumber)
        clearmi = False
        cnt = 0
        #TODO: not a good solution put message in queue, schedule a future event to retry yhe first item in queueu
        while(clearmi == False):
            clearmi, powerdb  = ahcuhd.ischannelclear(threshold=-35)
            print("Component:", self.componentinstancenumber, "clear mi=", clearmi)
            if  clearmi == True:
                evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
                self.send_down(evt)
            else:
                cnt = cnt + 1
                time.sleep(random.randrange(0,math.pow(2,cnt))*0.01)

class UsrpNode(ComponentModel):
    counter = 0
    def on_init(self, eventobj: Event):
        pass
    
    def on_message_from_top(self, eventobj: Event):
    # print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    
    def on_message_from_bottom(self, eventobj: Event):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        print(f"I am {self.componentname}.{self.componentinstancenumber}, received eventcontent=Component:{eventobj.eventcontent.header.messagefrom}{eventobj.eventcontent.payload}\n")    
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload
        #print(f"I am {self.componentname}.{self.componentinstancenumber}, sending down eventcontent={eventobj.eventcontent.payload}\n")
        self.send_down(evt)  # PINGPONG
    
    def on_startbroadcast(self, eventobj: Event):
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.BROADCAST, 0, 1)
        self.counter = self.counter + 1
        
        payload = "BMSG-" + str(self.counter)
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        # time.sleep(3)
        self.send_down(evt)
        # print("Starting broadcast")
    
    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentid)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentid)
    
        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.phy)
        self.phy.connect_me_to_component(ConnectorTypes.UP, self.appl)
    
        # Connect the bottom component to the composite component....
        # self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.appl.connect_me_to_component(ConnectorTypes.UP, self)
        self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)
    
        super().__init__(componentname, componentid)
        self.eventhandlers[UsrpNodeEventTypes.STARTBROADCAST] = self.on_startbroadcast

def main():
    topo = Topology()
# Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
# Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels(2, UsrpNode)
  # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
  
  # time.sleep(1)
  # topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

    topo.start()
    while(True):
        topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))
        time.sleep(0.1)


if __name__ == "__main__":
    main()
