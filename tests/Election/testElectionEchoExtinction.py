
import os
import sys
import time
import random
from enum import Enum
from graph import *
import numpy as np
sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from Ahc import ComponentModel, Event, ConnectorTypes, Topology
from Ahc import ComponentRegistry
from Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage, EventTypes
from Channels import P2PFIFOPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from NetworkLayers.AllSeeingEyeNetworkLayer import AllSeingEyeNetworkLayer

registry = ComponentRegistry()

topo = Topology()

message_count = 0



def main():
  # G = nx.Graph()
  # G.add_nodes_from([1, 2])
  # G.add_edges_from([(1, 2)])
  # nx.draw(G, with_labels=True, font_weight='bold')
  # plt.draw()
  global message_count
  fig, axes = plt.subplots(1, 7)
  fig.set_figheight(5)
  fig.set_figwidth(10)
  fig.tight_layout()
  time_arr = []
  message_count_arr = []

  for i in range(4, 9):

    start_time = time.time()

    g = Grid(i, ax= axes[i-4])
    topo.construct_from_graph(g.G, AdHocNode, P2PFIFOPerfectChannel)
    topo.start()
    for i in range(0,10):
      topo.nodes[i].initiate_process()

    end_time = time.time()
    time_arr.append(end_time-start_time)

    message_count_arr.append(message_count)
    message_count = 0

    g.plot()


  axes[5].plot(np.array([n**2 for n in range(4,9)]), np.array(message_count_arr))
  axes[6].plot(np.array([n**2 for n in range(4,9)]), np.array(time_arr))
  axes[5].set_ylabel('Messeage Count')
  axes[5].set_xlabel('Node Count')
  axes[6].set_ylabel('Time Passes in Seconds')
  axes[6].set_xlabel('Node Count')
  axes[5].set_title("Message Count by Node Count")
  axes[5].set_title("Time")
  plt.show()
  # plt.show()  # while (True): pass

if __name__ == "__main__":
  main()