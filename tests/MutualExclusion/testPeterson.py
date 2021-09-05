import matplotlib.pyplot as plt
import networkx as nx

from MutualExclusion.Peterson import *
from Ahc import ComponentModel, Event, EventTypes, ConnectorTypes, Topology
from Channels.Channels import FIFOBroadcastPerfectChannel

class AdHocNode(ComponentModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    print("Outgoing Message from ", self.componentinstancenumber, ". Node")
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    print("Incoming Message to ", self.componentinstancenumber, ". Node, From: ", eventobj.eventcontent.header.messagefrom)
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid, type):
    if type == 0:
      self.mainComponent = ProducerConsumerComponent("ProducerComponent", componentid,PetersonMessageTypes.INC)
      self.mainComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
    elif type == 1:
      self.mainComponent = ProducerConsumerComponent("ConsumerComponent", componentid,PetersonMessageTypes.DEC)
      self.mainComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
    elif type == 2:
      self.mainComponent = ResourceComponent("ResourceComponent", componentid)
      self.connect_me_to_component(ConnectorTypes.UP, self.mainComponent)
    super().__init__(componentname, componentid)

start = time.time()
G = nx.random_geometric_graph(3,1)
nx.draw(G, with_labels=True, font_weight='bold')
plt.draw()

topo = Topology()
#TODO: NodeTypes are not defined in AHC! Correct this implementation for implementing different NodeModels instead of types
topo.construct_from_graph_peterson(G, AdHocNode, FIFOBroadcastPerfectChannel)
topo.start()

time.sleep(1)
topo.nodes[0].mainComponent.start()
topo.nodes[1].mainComponent.start()
plt.show()

while (not topo.nodes[0].mainComponent.done): 
  time.sleep(0.1)
  
while (not topo.nodes[1].mainComponent.done):
  time.sleep(0.1)

print(f"{time.time() - start} s passed.")
print(topo.nodes[2].mainComponent)
