import os
import sys
import time
sys.path.insert(0, os.getcwd())
import networkx as nx
from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology, mp_construct_sdr_topology_without_channels
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel


class A(GenericModel):
  def on_init(self, eventobj: Event):
    if self.componentinstancenumber == 0:
      evt = Event(self, EventTypes.MFRT, "A to lower layer")
      self.send_down(evt)

  def on_message_from_bottom(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")

class B(GenericModel):
  def on_init(self, eventobj: Event):
    if self.componentinstancenumber == 0:
      evt = Event(self, EventTypes.MFRP, "B to peers")
      self.send_peer(evt)

  def on_message_from_top(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")

  def on_message_from_bottom(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
    evt = Event(self, EventTypes.MFRB, "B to higher layer")
    self.send_up(evt)

  def on_message_from_peer(self, eventobj: Event):
    print(f"I am {self.componentname}, got message from peer, eventcontent={eventobj.eventcontent}\n")

class N(GenericModel):
  
  def on_message_from_top(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
    evt = Event(self, EventTypes.MFRT, "N to lower layer")
    self.send_down(evt)

  def on_message_from_bottom(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")

  def on_message_from_peer(self, eventobj: Event):
    print(f"I am {self.componentname}, got message from peer, eventcontent={eventobj.eventcontent}\n")

class L(GenericModel):
  def on_message_from_top(self, eventobj: Event):
    print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}")
    evt = Event(self, EventTypes.MFRB, "L to higher layer")
    self.send_up(evt)
    evt = Event(self, EventTypes.MFRT, "L to channel")
    self.send_down(evt)

class Node(GenericModel):
  def on_init(self, eventobj: Event):
    #print(self.componentname, "-", self.componentinstancenumber, " received ", eventobj.event)
    pass

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    print(self.componentname, "-", self.componentinstancenumber, " received ", eventobj.event)
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn)
    # SUBCOMPONENTS
    self.A = A("A", componentinstancenumber, topology=topology)
    self.N = N("N", componentinstancenumber, topology=topology)
    self.B = B("B", componentinstancenumber, topology=topology)
    self.L = L("L", componentinstancenumber, topology=topology)

    self.components.append(self.A)
    self.components.append(self.N)
    self.components.append(self.B)
    self.components.append(self.L)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.A.connect_me_to_component(ConnectorTypes.DOWN, self.B)
    self.A.connect_me_to_component(ConnectorTypes.DOWN, self.N)

    self.N.connect_me_to_component(ConnectorTypes.UP, self.A)
    self.B.connect_me_to_component(ConnectorTypes.UP, self.A)

    self.N.connect_me_to_component(ConnectorTypes.PEER, self.B)
    self.B.connect_me_to_component(ConnectorTypes.PEER, self.N)

    self.B.connect_me_to_component(ConnectorTypes.DOWN, self.L)
    self.N.connect_me_to_component(ConnectorTypes.DOWN, self.L)

    self.L.connect_me_to_component(ConnectorTypes.UP, self.B)
    self.L.connect_me_to_component(ConnectorTypes.UP, self.N)

    # Connect the bottom component to the composite component....
    self.L.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.L)

def main():
  topo = Topology()

  numnodes = 10
  mp_construct_sdr_topology_without_channels( numnodes, Node, topo )
  topo.start()
  time.sleep(1)
  topo.exit()


if __name__ == "__main__":
  main()
