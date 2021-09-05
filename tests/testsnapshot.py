#!/usr/bin/env python3

from Channels.Channels import Channel
from Snapshot.Snapshot import ChandyLamportComponentModel, LaiYangComponentModel
from Snapshot.Snapshot import SnapshotEventTypes
from Ahc import Event, Topology
import matplotlib.pyplot as plt
import networkx as nx


def main():
    topo = Topology()
    topo.construct_sender_receiver(ChandyLamportComponentModel,
                                   ChandyLamportComponentModel, Channel)
    nx.draw(topo.G, with_labels=True, font_weight='bold')
    plt.draw()
    topo.start()
    topo.sender.send_self(Event(topo.sender, SnapshotEventTypes.TS, None))
    plt.show()

    topo.construct_sender_receiver(LaiYangComponentModel,
                                   LaiYangComponentModel, Channel)
    nx.draw(topo.G, with_labels=True, font_weight='bold')
    plt.draw()
    topo.start()
    topo.sender.send_self(Event(topo.sender, SnapshotEventTypes.TS, None))
    plt.show()


if __name__ == "__main__":
    exit(main())
