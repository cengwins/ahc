import os
import sys
import time
from enum import Enum
sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessage, GenericMessageHeader
from Ahc import ComponentRegistry
from PhysicalLayers.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
registry = ComponentRegistry()
from Channels.Channels import FIFOBroadcastPerfectChannel


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
    pass


  def on_message_from_top(self, eventobj: Event):
    #print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
    evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
    self.send_down(evt)
    pass



class UsrpNode(ComponentModel):
  counter = 0
  def on_init(self, eventobj: Event):
    pass

  def on_message_from_top(self, eventobj: Event):
    #print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    evt = Event(self, EventTypes.MFRB, eventobj.eventcontent)
    self.send_up(evt)
    self.counter = self.counter + 1
    evt.eventcontent.payload = "Component:" + str(self.componentinstancenumber) + "BMSG-" + str(self.counter)
    time.sleep(1)
    #print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent)) #PINGPONG

  def on_startbroadcast(self, eventobj: Event):
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.BROADCAST, 0, 1)
    payload = "BMSG-1"
    broadcastmessage = GenericMessage(hdr, payload)
    evt = Event(self, EventTypes.MFRT, broadcastmessage)
    time.sleep(3)
    self.send_down(evt)
    print("Starting broadcast")

  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentid)
    self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.phy)
    self.phy.connect_me_to_component(ConnectorTypes.UP, self.appl)

    # Connect the bottom component to the composite component....
    #self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
    #self.connect_me_to_component(ConnectorTypes.UP, self.phy)
    self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)

    super().__init__(componentname, componentid)
    self.eventhandlers[UsrpNodeEventTypes.STARTBROADCAST] = self.on_startbroadcast



def main():
  topo = Topology()
  # Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
  # Therefore, the usrps have to have names winslab_b210_x where x \in (0 to nodecount-1)
  topo.construct_winslab_topology_without_channels(4, UsrpNode)
  #topo.construct_winslab_topology_with_channels(4, UsrpNode, FIFOBroadcastPerfectChannel)
  
  time.sleep(1)
  topo.nodes[0].send_self(Event(topo.nodes[0], UsrpNodeEventTypes.STARTBROADCAST, None))

  topo.start()
  
  while(True):
    time.sleep(1)

if __name__ == "__main__":
  main()
