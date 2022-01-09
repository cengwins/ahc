import csv
import os
import random
import sys
import time

sys.path.insert(0, os.getcwd())

import networkx as nx
from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel

from Routing.TORA.tora import (
    RoutingTORAComponent,
    TORAHeight,
    heights,
    set_benchmark_time,
    wait_for_action_to_complete,
)


def average(l):
    sum = 0
    for value in l:
        sum = sum + value

    return sum / len(l)


def test(n: int):
    G = nx.connected_watts_strogatz_graph(n, 4, 0.10)
    topo = Topology()
    topo.construct_from_graph(G, RoutingTORAComponent, P2PFIFOPerfectChannel)
    source_id, destination_id = random.randint(0, n - 1), random.randint(
        0, n - 1
    )
    while destination_id == source_id:
        destination_id = random.randint(0, n - 1)
    destination_height: TORAHeight = TORAHeight(0, 0, 0, 0, destination_id)
    topo.start()

    t = time.time()
    set_benchmark_time()
    topo.nodes[destination_id].set_height(destination_height)
    topo.nodes[source_id].init_route_creation(destination_id)
    creation_time = wait_for_action_to_complete() - t

    message_times = []
    for _ in range(10):
        t = time.time()
        set_benchmark_time()
        topo.nodes[source_id].send_message(destination_id, "Test message")
        message_time = wait_for_action_to_complete() - t
        message_times.append(message_time)

    return creation_time, average(message_times), heights(topo)[source_id][1]


def main():
    n = 25
    cur_creation_times = []
    cur_message_times = []
    cur_heights = []
    for _ in range(6):
        creation_time, message_time, height = test(n)
        cur_message_times.append(message_time)
        cur_creation_times.append(creation_time)
        cur_heights.append(height)
    file = open("./wattz.csv", "a")
    writer = csv.writer(file)
    writer.writerow(
        (
            n,
            average(cur_creation_times),
            average(cur_message_times),
            average(cur_heights),
        )
    )


if __name__ == "__main__":
    main()
