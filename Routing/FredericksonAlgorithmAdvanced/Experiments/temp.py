from timeit import default_timer as timer
import pickle
from itertools import combinations, groupby
import networkx as nx
import random
import matplotlib.pyplot as plt

exit()


def draw_random_graph(n):
    """
    Draw a random graph with 2**i nodes,
    and p=i/(2**i)
    """
    k = True
    while k == True:
        k = False
        g_random = nx.gnp_random_graph(n, 0.3)
        if not nx.is_connected(g_random):
            k = True

    nx.draw(g_random, node_size=20)
    for e in g_random.edges:
        print(f"{e}")
    plt.show()
    plt.close()

draw_random_graph(10)