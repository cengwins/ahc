from DSDV import *


def graph_1():
    G = nx.Graph()
    G.add_nodes_from([1,2,3,4])
    G.add_edges_from([
        (1,2),
        (1,3),
        (2,3),
        (2,4)
    ])
    return G

def graph_2():
    G = nx.Graph()
    G.add_nodes_from([1,2,3,4,5,6])
    G.add_edges_from([
        (1,2),
        (1,3),
        (2,3),
        (2,4),
        (3,5),
        (1,6)
    ])
    return G

def result():
    base_path = ""
    throughput_path = "log_throughput_%d.txt"
    all_data = []
    for i in range(1,11):
        path = base_path + throughput_path % i
        data = None
        with open(path, "r") as f:
            data = f.read().split("\n")
        if data[-1] == "":
            data.pop()
        
        entries = list()
        for point in data:
            sec, size = point.split('\t')
            entries.append([int(float(sec)), int(size)])
        all_data += entries
    all_data.sort(key=lambda x: x[0])
    d = dict()
    for entry in all_data:
        if entry[0] in d:
            d[entry[0]] += entry[1]
        else:
            d[entry[0]] = entry[1]
    
    first_ts = min(d.keys())
    x = list()
    y = list()
    avg = list()
    for i,j in d.items():
        if i - first_ts >= 60:
            break
        x.append(i - first_ts)
        y.append(j)
        avg.append(sum(y) / len(y))

    plt.plot(x, y, label = "Throughput Weight", color='lightblue', linewidth = 3, marker='o', markerfacecolor='blue', markersize=4)
    plt.plot(x, avg, label = "Average Throughput Weight", color='red', linewidth = 1, marker='o', markerfacecolor='red', markersize=4)
    plt.xlabel('Seconds')
    # naming the y axis
    plt.ylabel('Throughput size of all nodes')
    # giving a title to my graph
    plt.title('Network Throughput Weight')
    
    # show a legend on the plot
    plt.legend(loc='upper left')
    
    # function to show the plot
    plt.show()

def main():

    base_path = ""
    graphs = [graph_2]
    for graph in graphs:
        G = graph()
        
        plt.draw()
        topo = Topology()
        topo.construct_from_graph(G, DSDVNode, P2PFIFOPerfectChannel, dynamic=True, path= base_path + "topology.txt")
        topo.start()
        
        sleep(60)
        nx.draw(topo.G, with_labels=True, font_weight='bold')
        plt.show()
    #plt.show()

if __name__ == "__main__":
    result()