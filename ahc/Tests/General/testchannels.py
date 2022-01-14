import os
import sys
import time
import pdb, traceback, sys

from ahc.Channels.Channels import P2PFIFOPerfectChannel
sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from ahc.Ahc import ComponentModel, Event, Topology, ComponentRegistry, GenericMessage, GenericMessageHeader, EventTypes

registry = ComponentRegistry()

class Sender(ComponentModel):
  def on_init(self, eventobj: Event):
    self.sendcnt = 0
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    self.send_self(Event(self, "generatemessage", "..."))

  def on_generate_message(self, eventobj: Event):
    self.sendcnt = self.sendcnt + 1
    msg = GenericMessage(GenericMessageHeader("AL", 0, 1), str(self.sendcnt))
    self.send_down(Event(self, EventTypes.MFRT, msg))
    time.sleep(0.1)
    self.send_self(Event(self, "generatemessage", "..."))

  def on_message_from_bottom(self, eventobj: Event):
    self.recvcnt = self.recvcnt + 1
    self.sentcnt = int(eventobj.eventcontent.payload)
    print(f"{self.recvcnt / self.sentcnt}")

  def __init__(self, componentname, componentinstancenumber):
    super().__init__(componentname, componentinstancenumber)
    self.eventhandlers["generatemessage"] = self.on_generate_message

class Receiver(ComponentModel):
  def on_init(self, eventobj: Event):
    self.recvcnt = 0
    print("Received Percentage:\n")

  def on_message_from_bottom(self, eventobj: Event):
    self.recvcnt = self.recvcnt + 1
    self.sentcnt = int(eventobj.eventcontent.payload)
    print(f"{self.recvcnt / self.sentcnt}")
    # print(nx.adjacency_matrix(Topology().G).todense())
    # print("Progress {:2.2}".format(self.recvcnt/self.sentcnt), end="\r")
    #Topology().shortest_path_to_all(self.componentinstancenumber)

def main():
  topo = Topology()

  topo.construct_sender_receiver(Sender, Sender, P2PFIFOPerfectChannel)
  nx.draw(topo.G, with_labels=True, font_weight='bold')
  plt.draw()

  # topo.computeForwardingTable()

  topo.start()
  plt.show()
  # while (True): pass   #plt.show() handles this

if __name__ == "__main__":
  try:
    main()
  except:
    extype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
