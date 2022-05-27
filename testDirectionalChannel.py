import os
import sys
import time
import pdb, traceback, sys


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel


import networkx as nx
import matplotlib.pyplot as plt


class SenderReceiver(GenericModel):
  def on_init(self, eventobj: Event):
    logger.applog(f"Initialized {self.componentname}-{self.componentinstancenumber}")

    if self.componentinstancenumber == 0:
      self.send_self(Event(self, "generatemessage", "..."))

  def sendmessage(self):
    self.sentcnt = self.sentcnt + 1
    msg = GenericMessage(GenericMessageHeader("AL", 0, 1), str(self.sentcnt))
    self.send_down(Event(self, EventTypes.MFRT, msg))

  def on_generate_message(self, eventobj: Event):
    self.sendmessage()
    time.sleep(0.001)
    self.send_self(Event(self, "generatemessage", "..."))

  def on_message_from_bottom(self, eventobj: Event):
    logger.debug(self.componentname, self.componentinstancenumber, " RECEIVED ", str(eventobj))
    self.recvcnt = self.recvcnt + 1
    sentcounter = int(eventobj.eventcontent.payload)
    logger.applog(f"{self.componentinstancenumber}: ratio={self.recvcnt / sentcounter} [{self.recvcnt}, {sentcounter}]")

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    self.eventhandlers["generatemessage"] = self.on_generate_message
    self.sentcnt = 0
    self.recvcnt = 0


def main():
  setAHCLogLevel(21)
  topo = Topology()
  topo.construct_sender_receiver_directional(SenderReceiver, SenderReceiver, GenericChannel)
  #nx.draw(topo.G, with_labels=True, font_weight='bold')
  #plt.draw()

  # topo.computeForwardingTable()

  topo.start()
  time.sleep(5)
  topo.exit()
  

if __name__ == "__main__":
  try:
    main()
  except:
    extype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
