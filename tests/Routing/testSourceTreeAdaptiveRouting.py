import csv
import random
import threading
import time
from collections import Counter

from Routing.SourceTreeAdaptiveRouting.helper import STARTestBenchConfig

import networkx as nx

from Ahc import Topology, ComponentModel, Event, EventTypes, ConnectorTypes, ComponentRegistry
from Channels.Channels import FIFOBroadcastPerfectChannel
from LinkLayers.GenericLinkLayer import LinkLayer
from Routing.SourceTreeAdaptiveRouting.ApplicationComponent import ApplicationComponent
from Routing.SourceTreeAdaptiveRouting.STARNodeComponent import STARNodeComponent


class AdHocNode(ComponentModel):

    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)

        self.application_layer = ApplicationComponent("ApplicationLayer", componentid)
        self.star = STARNodeComponent("STARNode", componentid)
        self.link_layer = LinkLayer("LinkLayer", componentid)

        self.application_layer.connect_me_to_component(ConnectorTypes.DOWN, self.star)
        self.star.connect_me_to_component(ConnectorTypes.UP, self.application_layer)
        self.star.connect_me_to_component(ConnectorTypes.DOWN, self.link_layer)
        self.link_layer.connect_me_to_component(ConnectorTypes.UP, self.star)

        self.link_layer.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.link_layer)

    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))


class TestBench:
    def draw_random_connected_graph(self, n):
        terminate = False

        while not terminate:
            G = nx.gnp_random_graph(n, STARTestBenchConfig.DENSITY)
            terminate = nx.is_connected(G)

        return G

    def draw_graph(self):
        G = self.draw_random_connected_graph(STARTestBenchConfig.NODE_COUNT)

        for (u, v, w) in G.edges(data=True):
            w['weight'] = random.randint(1, 20)

        return G

    def terminate_all(self):
        components = ComponentRegistry().components.values()

        for c in components:
            c.terminate()

        STARTestBenchConfig.TERMINATED = True

    def menu(self):
        print('\n---------------------------')
        print('1- Show routing tables')
        print('2- Show topology graph of Y in node X')
        print('3- Show source tree of Y in node X')
        print('4- Build shortest path tree in node X')
        print('5- Send message to X')
        print('6- Show stats')
        print('9- Quit')
        selection = int(input('Select: '))

        if selection == 1:
            N = len(Topology().nodes)
            for i in range(0, N):
                ComponentRegistry().get_component_by_key("STARNode", i).show_routing_table()
            return True
        elif selection == 2:
            X, Y = list(map(int, input('X Y:').split(' ')))
            ComponentRegistry().get_component_by_key("STARNode", X).show_topology_graph(Y)
            return True
        elif selection == 3:
            X, Y = list(map(int, input('X Y:').split(' ')))
            ComponentRegistry().get_component_by_key("STARNode", X).show_source_tree(Y)
            return True
        elif selection == 4:
            X = int(input('X:'))
            comp: STARNodeComponent = ComponentRegistry().get_component_by_key("STARNode", X)
            comp.build_shortest_path_tree(X)
            comp.show_source_tree(X)
            return True
        elif selection == 5:
            frm, to = list(map(int, input('From To:').split(' ')))
            msg = input('Message: ')
            comp: ApplicationComponent = ComponentRegistry().get_component_by_key("ApplicationLayer", frm)
            comp.send(to, msg)
            return True
        elif selection == 6:
            N = len(Topology().nodes)
            counter = Counter()

            for n in range(0, N):
                comp: STARNodeComponent = ComponentRegistry().get_component_by_key("STARNode", n)
                stats = comp.stats.get_stats()
                counter.update(stats)

            print(counter)
            return True
        else:
            return False

    def main(self):
        threading.Timer(STARTestBenchConfig.SIMULATION_TIME, self.terminate_all).start()
        graph = self.draw_graph()
        topology = Topology()
        topology.construct_from_graph(graph, AdHocNode, FIFOBroadcastPerfectChannel)
        topology.start()
        # topology.plot()

        while not STARTestBenchConfig.TERMINATED or self.menu():
            time.sleep(1)


if __name__ == '__main__':
    TestBench().main()
