import os
import sys
import time
sys.path.insert(0, os.getcwd())
import networkx as nx
from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
import queue
from multiprocessing import Manager, freeze_support


class A(GenericModel):
  def on_init(self, eventobj: Event):
    #if self.componentinstancenumber == 0:
    print(f"I am {self.componentname}-{self.componentinstancenumber}, eventcontent={eventobj.eventcontent}")
    time.sleep(1)
    for i in range(5):
      evt = Event(self, EventTypes.MFRT, "TO CHANNEL" + str(i))
      self.send_down(evt)
  def on_message_from_bottom(self, eventobj: Event):
      print(f"I am {self.componentname}-{self.componentinstancenumber}, eventcontent={eventobj.eventcontent}")

class Node(GenericModel):
  def on_init(self, eventobj: Event):
    #print(self.componentname, "-", self.componentinstancenumber, " received ", eventobj.event)
    pass

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    #print("send_down at on_message_from_top", self.componentname, self.componentinstancenumber )
    

  def on_message_from_bottom(self, eventobj: Event):
    print(self.componentname, "-", self.componentinstancenumber, " received ", eventobj.event)
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, child_conn, node_queues, channel_queues)
    # SUBCOMPONENTS

    self.A = A("A", componentinstancenumber, topology=topology)
    self.components.append(self.A)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.A.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.A)

def main():
  set_start_method = "fork";
  topo = Topology()

  # numnodes = 10
  # topo.mp_construct_sdr_topology_without_channels( numnodes, Node )
  # topo.start()
  # time.sleep(1)
  # topo.exit()

  #G = nx.random_geometric_graph(5, 0.5)
  G =nx.Graph()
  G.add_node(0)
  G.add_node(1)
  G.add_node(2)
  G.add_edge(0,1)
  G.add_edge(1,0)
  G.add_edge(0,2)
  G.add_edge(2,0)
  G.add_edge(1,2)
  G.add_edge(2,1)
  

  manager = Manager()
  topo.mp_construct_sdr_topology(G, Node, GenericChannel,manager)
  topo.start()
  while(True):
    time.sleep(1)
  topo.exit()


if __name__ == "__main__":
  freeze_support()
  main()
