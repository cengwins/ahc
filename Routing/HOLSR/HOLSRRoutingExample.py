import time, os, sys
sys.path.insert(0, os.getcwd())

from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

from Routing.HOLSR.HOLSRComponent import HOLSRComponent
from Routing.HOLSR.utils import random_directed_graph, random_layered_graph, Tracing, RepeatDeltaTimer

import networkx as nx
import matplotlib.pyplot as plt


def main():
    graph,layers = random_layered_graph(25)
    topology = Topology()
    topology.construct_from_graph(graph, HOLSRComponent, P2PFIFOPerfectChannel)
    topology.start()

    RepeatDeltaTimer().set_interval(0.25)
    RepeatDeltaTimer().start()

    plt.figure(1)
    plt.clf()
    fig, ax = plt.subplots(3, 2, num=1)
    pos = nx.spring_layout(graph)
    nx.draw_networkx(graph, pos=pos, ax=ax[0, 0])

    time.sleep(10)
    RepeatDeltaTimer().cancel()

    for i in range(4):
        nx.draw_networkx(Tracing().step_to_graph(i), pos=pos, ax=ax[int(int(i + 1) / 2), int(int(i + 1) % 2)])
    nx.draw_networkx(Tracing().to_graph(), pos=pos, ax=ax[2, 1])

    plt.setp(ax, xlim=ax[0, 0].get_xlim(), ylim=ax[0, 0].get_ylim())
    plt.draw()
    plt.show()

    print("done.")
    time.sleep(10000)

# def main():
#     graph, sep = random_layered_graph(25)
#     plt.figure(1)
#     plt.clf()
#     fig, ax = plt.subplots(2, 2, num=1)
#     pos = nx.spring_layout(graph)
#     nx.draw_networkx(graph,  pos=pos, ax=ax[0, 0], node_color='g')

#     nx.draw_networkx(graph,  pos=pos, ax=ax[0, 1], node_color='g', alpha=0.2)
#     nx.draw_networkx(sep[0], pos=pos, ax=ax[0, 1], node_color='r')

#     nx.draw_networkx(graph,  pos=pos, ax=ax[1, 0], node_color='g', alpha=0.2)
#     nx.draw_networkx(sep[1], pos=pos, ax=ax[1, 0], node_color='r')

#     nx.draw_networkx(graph,  pos=pos, ax=ax[1, 1], node_color='g', alpha=0.2)
#     nx.draw_networkx(sep[2], pos=pos, ax=ax[1, 1], node_color='r')
#     plt.setp(ax, xlim=ax[0, 0].get_xlim(), ylim=ax[0, 0].get_ylim())
#     plt.show()
#     time.sleep(100000)

if __name__ == '__main__':
    main()
