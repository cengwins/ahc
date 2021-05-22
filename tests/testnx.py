import os
import sys

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

def main():
  inf = float('inf')

  G = nx.erdos_renyi_graph(5, 0.55)
  N = len(G.nodes)
  ForwardingTable = [[0 for i in range(N)] for j in range(N)]
  path = dict(nx.all_pairs_shortest_path(G))
  print(f"There are {len(G.nodes)} nodes")
  for i in range(len(G.nodes)):
    for j in range(len(G.nodes)):
      try:
        mypath = path[i][j]
        # print(f"{i}to{j} path = {path[i][j]} nexthop = {path[i][j][1]}")
        ForwardingTable[i][j] = path[i][j][1]
      except KeyError:
        # print(f"{i}to{j}path = NONE")
        ForwardingTable[i][j] = inf  # No paths
      except IndexError:
        # print(f"{i}to{j} nexthop = NONE")
        ForwardingTable[i][j] = i  # There is a path but length = 1 (self)

  print('\n'.join([''.join(['{:3}'.format(item) for item in row])
                   for row in ForwardingTable]))

  nx.draw(G, with_labels=True, font_weight='bold')
  plt.show()

if __name__ == "__main__":
  main()
