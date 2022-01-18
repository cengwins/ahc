import random
import networkx as nx
import matplotlib.pyplot as plt

class ERG:
    def __init__(self, node_count: int, connectivity: float, ax = None) -> None:
        self.ax = ax
        self.node_count = node_count
        self.root = random.choice(list(range(self.node_count)))
        self.G = nx.nx.erdos_renyi_graph(self.node_count, connectivity, seed=random.randint(100, 10000), directed=False)

    def plot(self):
        node_colors = ["red" if i == self.root else "mediumslateblue" for i in range(self.node_count)]

        if self.ax is not None:
            nx.draw(self.G, with_labels=True, node_color=node_colors, ax=self.ax)
        else:
            nx.draw(self.G, with_labels=True, node_color=node_colors)

class Grid:
    def __init__(self, node_count_on_edge: int, ax = None) -> None:
        self.ax = ax
        self.node_count_on_edge = node_count_on_edge
        self.root = random.choice(list(range(self.node_count_on_edge ** 2)))
        self.G = nx.grid_2d_graph(self.node_count_on_edge, self.node_count_on_edge)
        self.positions = {self.node_count_on_edge * x[0] + x[1]: x for x in self.G.nodes()}
        
        self.G = nx.relabel_nodes(self.G, lambda x: self.node_count_on_edge * x[0] + x[1])
        
    def plot(self):
        node_colors = ["red" if i == self.root else "mediumslateblue" for i in range(self.node_count_on_edge ** 2)]

        if self.ax is not None:
            nx.draw(self.G, with_labels=True, node_color=node_colors, pos=self.positions, ax=self.ax)
        else:
            nx.draw(self.G, with_labels=True, node_color=node_colors, pos=self.positions)

class Star:
    def __init__(self, slave_count: int, master_is_root: bool = True, ax = None) -> None:
        self.ax = ax
        self.slave_count = slave_count
        self.root = 0 if master_is_root else random.choice(list(range(1, slave_count + 1)))

        self.G = nx.Graph()

        self.G.add_node(0)

        for i in range(1, self.slave_count + 1):
            self.G.add_node(i)
            self.G.add_edge(0, i)
        
    def plot(self):
        node_colors = ["red" if i == self.root else "mediumslateblue" for i in range(self.slave_count + 1)]

        if self.ax is not None:
            nx.draw(self.G, with_labels=True, node_color=node_colors, ax=self.ax)
        else:
            nx.draw(self.G, with_labels=True, node_color=node_colors)

if __name__ == "__main__":
    fig, axes = plt.subplots(1, 4)
    fig.set_figheight(5)
    fig.set_figwidth(25)
    fig.tight_layout()

    ERG(10, 0.45, ax=axes[0]).plot()
    Grid(4, ax=axes[1]).plot()
    Star(6, master_is_root=True, ax=axes[2]).plot()
    Star(6, master_is_root=False, ax=axes[3]).plot()

    plt.show()