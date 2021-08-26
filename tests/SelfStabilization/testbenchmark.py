import os
import sys

sys.path.insert(0, os.getcwd())

import time

import matplotlib.pyplot as plt

from SelfStabilization.AroraGouda import *
from SelfStabilization.AfekKuttenYang import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def main():
  for n in range(15, 50 + 1):
    G = nx.random_geometric_graph(n, 0.8)

    topology1 = SharedMemoryTopology()
    topology1.construct_from_tree(G, AroraGoudaNode, args=[len(G.nodes)]) # K value

    topology2 = SharedMemoryTopology()
    topology2.construct_from_tree(G, AfekKuttenYangNode, args=[max(list(G.nodes))])

    eprint('started')

    start_time = time.monotonic()
    topology1.start()
    elapsed1 = time.monotonic() - start_time
    eprint('skip')

    start_time = time.monotonic()
    topology2.start()
    elapsed2 = time.monotonic() - start_time

    print(f'{elapsed1};{elapsed2}')
    eprint(f'{elapsed1};{elapsed2}')

if __name__ == "__main__":
  main()
