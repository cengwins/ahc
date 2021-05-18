#!/usr/bin/env python3

from Channels import Channel
from Snapshot import ChandyLamportComponentModel
from Ahc import Topology
import matplotlib.pyplot as plt
import networkx as nx


def main():
    topo = Topology()
    topo.construct_sender_receiver(ChandyLamportComponentModel,
                                   ChandyLamportComponentModel, Channel)
    nx.draw(topo.G, with_labels=True, font_weight='bold')
    plt.draw()
    topo.start()
    topo.sender.report_snapshot()
    plt.show()


if __name__ == "__main__":
    exit(main())
