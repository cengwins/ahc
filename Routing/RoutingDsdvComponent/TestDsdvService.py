import os
import sys
import random

sys.path.insert(0, os.getcwd())

import networkx as nx
from Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessageHeader, GenericMessage
from DsdvService import DsdvService, DataMessageTypes
from Channels.Channels import Channel
from LinkLayers.GenericLinkLayer import LinkLayer
from threading import Timer


class ApplicationLayerTimer():

  def __init__(self, interval, handleFunction):
    self.interval = interval
    self.handleFunction = handleFunction
    self.thread = Timer(self.interval, self.handleFunction)
    self.thread.daemon = True
    self.thread.start()

  def start(self, interval):
    self.thread = Timer(self.interval, self.handleFunction)
    self.thread.start()

  def cancel(self):
    self.thread.cancel()


class ApplicationLayer(ComponentModel):

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.t = ApplicationLayerTimer(12, self.generate_and_send_message)

  def send_message(self, dataToSend, destination):
    payload = dataToSend
    destination = destination
    header = GenericMessageHeader(DataMessageTypes.appData, self.componentinstancenumber, destination)

    message = GenericMessage(header, payload)
    self.send_down(Event(self, EventTypes.MFRT, message))

  def on_message_from_bottom(self, eventobj: Event):
    msg = eventobj.eventcontent
    hdr = msg.header
    payload = msg.payload
    print("I am: " + self.unique_name())
    print(payload)

  def generate_and_send_message(self):
    destinationAddress = random.randint(0, 4)

    if self.componentinstancenumber == 1:
      dataToSend = "It is the payload of the data packet send from " + self.unique_name() + " to: " + str(destinationAddress)
      self.send_message(dataToSend, destinationAddress)


class AdHocNode(ComponentModel):

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))


  def __init__(self, componentname, componentid):
    # SUBCOMPONENTS
    self.applicationLayer = ApplicationLayer("Application Layer", componentid)
    self.dsdvService = DsdvService("DSDV Service", componentid)
    self.linklayer = LinkLayer("LinkLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.applicationLayer.connect_me_to_component(ConnectorTypes.DOWN, self.dsdvService)
    self.dsdvService.connect_me_to_component(ConnectorTypes.UP, self.applicationLayer)

    self.dsdvService.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.dsdvService)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

    super().__init__(componentname, componentid)


def main():

  #G = nx.random_geometric_graph(5, 0.5)

  G = nx.Graph()
  G.add_nodes_from([0, 1, 2, 3, 4])
  G.add_edge(0, 4)
  G.add_edge(1, 2)
  G.add_edge(1, 3)
  G.add_edge(1, 4)
  G.add_edge(2, 4)


  topo = Topology()
  topo.construct_from_graph(G, AdHocNode, Channel)

  topo.start()
  topo.plot()

  # plt.show()
  while (True): pass

if __name__ == "__main__":
  main()