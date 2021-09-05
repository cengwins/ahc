import os
import sys
import time
from enum import Enum
sys.path.insert(0, os.getcwd())

from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload
from Ahc import ComponentRegistry
from PhysicalLayers.UsrpPhysicalLayer import  PhyUsrpB210OFDMPhysicalLayer
registry = ComponentRegistry()
from PhysicalLayers.Channels import FIFOBroadcastPerfectChannel


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
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")




class UsrpNode(ComponentModel):
  counter = 0
  def on_init(self, eventobj: Event):
    pass

  def on_message_from_top(self, eventobj: Event):
    print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    evt = Event(self, EventTypes.MFRB, eventobj.eventcontent)
    self.send_up(evt)
    self.counter = self.counter + 1
    evt.eventcontent.payload = "This is a broadcast message" + str(self.counter)
    print(f"I am {self.componentname}.{self.componentinstancenumber},sending down eventcontent={eventobj.eventcontent}\n")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent)) #PINGPONG

  def on_startbroadcast(self, eventobj: Event):
    hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.BROADCAST, 0, 1)
    payload = "This is a broadcast message 1"
    broadcastmessage = GenericMessage(hdr, payload)
    evt = Event(self, EventTypes.MFRT, broadcastmessage)
    time.sleep(3)
    self.send_down(evt)
  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentid)
    self.phy = PhyUsrpB210OFDMPhysicalLayer("PhyUsrpB210OFDMPhysicalLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.phy)
    self.phy.connect_me_to_component(ConnectorTypes.UP, self.appl)

    # Connect the bottom component to the composite component....
    self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.phy)
    self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)

    super().__init__(componentname, componentid)
    self.eventhandlers[UsrpNodeEventTypes.STARTBROADCAST] = self.on_startbroadcast



def main():
  topo = Topology()
  topo.construct_sender_receiver(UsrpNode,
                                 UsrpNode, FIFOBroadcastPerfectChannel)

  time.sleep(5)
  topo.sender.send_self(Event(topo.sender, UsrpNodeEventTypes.STARTBROADCAST, None))

  topo.start()
  while(True):
    time.sleep(1)

if __name__ == "__main__":
  main()
