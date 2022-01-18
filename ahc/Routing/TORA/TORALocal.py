import networkx as nx
import os
import sys
import random

sys.path.insert(0, os.getcwd())
import matplotlib.pyplot as plt
from random import randrange
import datetime
from time import sleep


from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes
from ahc.Ahc import ComponentRegistry
from ahc.Broadcasting.Broadcasting import ControlledFlooding
from ahc.Channels.Channels import P2PFIFOFairLossChannel
from ahc.LinkLayers.GenericLinkLayer import LinkLayer
from ahc.Routing import AllSeeingEyeNetworkLayer
from ahc.Ahc import ComponentModel
'''
Creating nodes -> demand driven
Maintaining routes -> link reversal algorithm
Erasing routes  -> to delete invalid nodes

Link Reversal -> if a edge has downstream -> do nothing
              -> if not reverse the link and continue until finding a edge that has a downstream
              -> if there is no edge has the downstream, there is a partition -> clear all edges

Attributes -> t -> time of update after link reversal
           -> oid -> who has the link reversal
           -> r -> reflection bit
           -> p -> height (dest 0)
           -> i -> unique id
'''


registry = ComponentRegistry()

class AdHocNode(ComponentModel):
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentid):

    # SUBCOMPONENTS
    self.broadcastservice = ControlledFlooding("SimpleFlooding", componentid)
    self.network = AllSeeingEyeNetworkLayer.AllSeingEyeNetworkLayer("NetworkLayer", componentid)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.broadcastservice.connect_me_to_component(ConnectorTypes.DOWN, self.network)
    self.network.connect_me_to_component(ConnectorTypes.UP, self.broadcastservice)

    # Connect the bottom component to the composite component....
    self.network.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.network)

    super().__init__(componentname, componentid)

#    self.eventhandlers[EventTypes.MFRT] = self.onMessageFromTop
#    self.eventhandlers["messagefromchannel"] = self.onMessageFromChannel

class TORA(ComponentModel):
  def TORATest1(self):
    G = nx.Graph()
    t = 1
    #Test 1
    ''' 
    G.add_edge(0, 1)
    G.add_edge(0, 2)
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(2, 4)
    G.add_edge(3, 4)
    G.add_edge(3, 5)
    G.add_edge(4, 6)
    G.add_edge(5, 6)
    #G.add_edge(5, 7)
  
    G.nodes[0]['i'] = 'A'
    G.nodes[1]['i'] = 'B'
    G.nodes[2]['i'] = 'C'
    G.nodes[3]['i'] = 'D'
    G.nodes[4]['i'] = 'E'
    G.nodes[5]['i'] = 'Y'
    G.nodes[6]['i'] = 'X'
    #G.nodes[7]['i'] = 'F'
  
    DG = nx.DiGraph()
    dest = 6
    source = 0
    create(G, DG, source, dest)
    for i in range(G.number_of_nodes()):
      print(DG.edges(i))
  
    # DG.remove_edge(4, 5)
    # G.remove_edge(4, 5)
    # link_reversal(G, DG, 4)
  
    DG.remove_edge(3, 2)
    G.remove_edge(2, 3)
    link_reversal(G, DG, 2, t)
  
    DG.remove_edge(2, 4)
    G.remove_edge(2, 4)
    link_reversal(G, DG, 2, t)
  
    '''
    #Test 2
    G.add_edge(0, 1)
    G.add_edge(0, 2)
    G.add_edge(1, 3)
    G.add_edge(1, 4)
    G.add_edge(4, 3)
    G.add_edge(2, 5)
    G.add_edge(4, 5)
    G.add_edge(3, 6)
    G.add_edge(6, 7)
    G.add_edge(5, 7)

    G.nodes[0]['i'] = 'C'
    G.nodes[1]['i'] = 'A'
    G.nodes[2]['i'] = 'G'
    G.nodes[3]['i'] = 'D'
    G.nodes[4]['i'] = 'B'
    G.nodes[5]['i'] = 'H'
    G.nodes[6]['i'] = 'E'
    G.nodes[7]['i'] = 'F'

    DG = nx.DiGraph()
    print(list(G.degree()))
    dest = 7
    source = 0
    self.create(G, DG, source, dest)
    for i in range(G.number_of_nodes()):
      print(DG.edges(i))

    nx.draw(DG, with_labels=True, font_weight='bold')
    plt.draw()
    plt.show()

    print("----------------- First Link Reversal -----------------")
    DG.remove_edge(4, 5)
    G.remove_edge(4, 5)
    self.link_reversal(G, DG, 4, t)

    print("----------------- Second Link Reversal -----------------")
    DG.remove_edge(3, 6)
    G.remove_edge(3, 6)
    self.link_reversal(G, DG, 3, t)

    print("----------------- Third Link Reversal -----------------")
    DG.remove_edge(0, 2)
    G.remove_edge(0, 2)
    self.link_reversal(G, DG, 0, t)

    print(DG.edges.data())


  def create(self, G, DG, source, i):
    start = datetime.datetime.now()
    flag = [0] * G.number_of_nodes()
    flag[i] = 1
    counter = [0] * G.number_of_nodes()
    nodes_array = []
    queue = []
    queue.append(i)
    while (queue):
      s = queue.pop(0)
      DG.add_node(s)
      nodes_array.append(s)
      for x in range(len(list(G.neighbors(s)))):
        if (DG.has_edge(s, list(G.neighbors(s))[x]) == False and s != source):
          DG.add_edge(list(G.neighbors(s))[x], s)
        if flag[list(G.neighbors(s))[x]] == 0:
          queue.append(list(G.neighbors(s))[x])
          flag[list(G.neighbors(s))[x]] = 1
          counter[list(G.neighbors(s))[x]] = counter[s] + 1

    for node in nodes_array:
      DG.nodes[node]['p'] = counter[node]
      DG.nodes[node]['r'] = 0
      DG.nodes[node]['oid'] = 0
      DG.nodes[node]['t'] = 0

    end = datetime.datetime.now()
    elapsed_time = end - start
    print("Elapsed Time :", elapsed_time.microseconds, "microseconds")
    return elapsed_time.microseconds


  def link_reversal(self, G, DG, node, t):
    start = datetime.datetime.now()
    queue = []
    queue.append(node)
    counter = 1
    reverse_flag = 0

    irreversible_count = 0
    #main_node_id = nx.get_node_attributes(G, 'i')[node]
    while (queue):
      node = queue.pop(0)
      irreversible_count = 0
      if (len(list(DG.neighbors(node))) == 0 or nx.get_node_attributes(DG, 'r')[node] == 1):
        print("Reversing link", node)
        if (len(list(G.neighbors(node))) == 0):
          print("There is no neighbour of ", node)
          print(node, "deleted.")
          DG.nodes[node]['p'] = counter - 1
          DG.remove_node(node)
          G.remove_node(node)
        else:
          DG.nodes[node]['t'] = t
          neighbour_arr = list(G.neighbors(node))
          print("Neighbours: ", neighbour_arr)
          for neighbour_node in neighbour_arr:
            if ((nx.get_node_attributes(DG, 't')[neighbour_node] != nx.get_node_attributes(DG, 't')[node] and
                nx.get_node_attributes(DG, 't')[neighbour_node] != 1) or
                nx.get_node_attributes(DG, 'r')[neighbour_node] != nx.get_node_attributes(DG, 'r')[node]):
              queue.append(neighbour_node)
              if(DG.has_edge(neighbour_node, node)):
                DG.remove_edge(neighbour_node, node)
                DG.add_edge(node, neighbour_node)
              if (nx.get_node_attributes(DG, 'r')[node] == 1):
                DG.nodes[neighbour_node]['r'] = 1
            else:
              print("Partial Reverse did not count : ", neighbour_node)
              irreversible_count += 1
              if (irreversible_count == len(list(G.neighbors(node))) and irreversible_count == 1 and
                  nx.get_node_attributes(DG, 'r')[node] != 1 and reverse_flag == 0):
                  if(len(list(G.neighbors(node))) != 1 ):
                    queue.append(node)
                    t += 1
                    counter = 2
                  else:
                    print("Could not find path. Reversal bit activated at", node)
                    queue.append(node)
                    t += 1
                    DG.nodes[node]['r'] = 1
                    counter = 2
                    reverse_flag = 1
              elif (irreversible_count == len(list(G.neighbors(node))) and irreversible_count > 1 and
                    nx.get_node_attributes(DG, 'r')[node] != 1):
                print("Could not find path. Reversal bit activated at", node)
                queue.append(node)
                DG.nodes[node]['r'] = 1
                counter = 2
              elif (irreversible_count == len(list(G.neighbors(node))) and nx.get_node_attributes(DG, 'r')[node] == 1):
                print("Detected partition. Clearing starts at ", node)
                clear_queue = []
                clear_queue.append(node)
                while (clear_queue):
                  clear_node = clear_queue.pop(0)
                  print(clear_node, "deleted.")
                  clear_neighbour_arr = list(G.neighbors(clear_node))
                  for clear_neighbour_node in clear_neighbour_arr:
                    if(nx.get_node_attributes(DG, 'r')[clear_neighbour_node] == 1):
                      if (clear_neighbour_node not in clear_queue):
                        clear_queue.append(clear_neighbour_node)
                      if (DG.has_edge(clear_node, clear_neighbour_node) == True):
                        DG.remove_edge(clear_node, clear_neighbour_node)
                      else:
                        DG.remove_edge(clear_neighbour_node, clear_node)
                      G.remove_edge(clear_node, clear_neighbour_node)
                  DG.remove_node(clear_node)
                  G.remove_node(clear_node)
                end = datetime.datetime.now()
                elapsed_time = end - start
                print("Elapsed Time :", elapsed_time.microseconds)
                return elapsed_time.microseconds
                #return 1 To calculate how much deletion has been done

          counter = counter - 1
          DG.nodes[node]['p'] = counter
          #DG.nodes[node]['oid'] = main_node_id

      else:
        print("Do nothing with", node)
    end = datetime.datetime.now()
    elapsed_time = end - start
    print("Elapsed Time :", elapsed_time.microseconds, "microseconds")
    return elapsed_time.microseconds
    #return 0

def TORATest2():
  tora = TORA("TORA", 1)
  G = nx.soft_random_geometric_graph(1000, 0.04)

  DG = nx.DiGraph()
  dest_array = [0] * G.number_of_nodes()
  for i in range(G.number_of_nodes()):
    for j in range(len(list(G.neighbors(i)))):
      dest_array[i] += 1

  max = 0
  for i in range(len(dest_array)):
    if (dest_array[i] > max):
      max = dest_array[i]
      dest = i

  source = 0
  elapsed_time_create = 0
  elapsed_time_create = tora.create(G, DG, source, dest)
  print(elapsed_time_create)
  nx.draw(DG, with_labels=True, font_weight='bold')
  plt.draw()
  plt.show()
  G = nx.Graph()
  for i in range(len(list(DG.edges))):
    G.add_edge(list(DG.edges)[i][0], list(DG.edges)[i][1])

  topo = Topology()
  topo.construct_from_graph(DG, AdHocNode, P2PFIFOFairLossChannel)
  for ch in topo.channels:
    topo.channels[ch].setPacketLossProbability(random.random())
    topo.channels[ch].setAverageNumberOfDuplicates(0)

  ComponentRegistry().print_components()

  topo.start()
  topo.plot()

  iteration = 0
  elapsed_time_main = 0
  one_operation = 0
  total_elapsed_time = 0
  while(len(list(DG.edges)) > 0 and iteration < 400):
    t = 1
    num_of_edges = DG.number_of_edges()
    rand = randrange(num_of_edges)
    print("--------------------------------------------------------------------------------------------------------------------------------------------------------")
    print(rand)
    removed_1 = list(DG.edges)[rand][0]
    removed_2 = list(DG.edges)[rand][1]
    DG.remove_edge(removed_1, removed_2)
    G.remove_edge(removed_1, removed_2)
    print(removed_1, removed_2)
    elapsed_time_main = tora.link_reversal(G, DG, removed_1, t)
    if(elapsed_time_main < 510):
      total_elapsed_time = total_elapsed_time
    else:
      total_elapsed_time = total_elapsed_time + elapsed_time_main - 500
    print("Size of graph :", len(list(DG.edges)))
    '''
    topo.construct_from_graph(DG, AdHocNode, P2PFIFOFairLossChannel)
    for ch in topo.channels:
      topo.channels[ch].setPacketLossProbability(random.random())
      topo.channels[ch].setAverageNumberOfDuplicates(0)

    ComponentRegistry().print_components()

    topo.start()
    topo.plot()
    '''
    iteration += 1
    sleep(0.05)
  print("Number of Iterations:", iteration)
  print("Total Elapsed Time:", total_elapsed_time, "microseconds")

if __name__ == '__main__':
  #tora = TORA("TORA", 1)
  #tora.TORATest1()
  TORATest2()
