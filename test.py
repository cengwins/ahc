import os
import sys
import time
import random
from enum import Enum
sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.NetworkLayer.GenericNetworkLayer import GenericNetworkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel


# define your own message types
class ApplicationLayerMessageTypes(Enum):
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    def __str__(self) -> str:
        return "ApplicationLayerMessageHeader"


# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    def __str__(self) -> str:
        return "ApplicationLayerMessagePayload"


class ApplicationLayerComponent(GenericModel):
    

    def send_message(self):
        destination = 1
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber,
                                                destination)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr, payload)
        self.send_self(Event(self, "propose", proposalmessage))

    def on_init(self, eventobj: Event):
        if self.componentinstancenumber == 0:
            self.t = AHCTimer(0.1, self.send_message)
            self.t.start()
        else:
            pass

    def on_message_from_bottom(self, eventobj: Event):
        try:
            applmessage = eventobj.eventcontent
            hdr = applmessage.header
            if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                logger.applog(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
            elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
                logger.applog(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        except AttributeError:
            logger.error("Attribute Error")

    # logger.applog(f"{self.componentname}.{self.componentinstancenumber}: Gotton message {eventobj.content} ")
    # value = eventobj.content.value
    # value += 1
    # newmsg = MessageContent( value )
    # myevent = Event( self, "agree", newmsg )
    # self.trigger_event(myevent)

    def on_propose(self, eventobj: Event):
        destination = 1
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber,
                                            destination)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))

    def on_agree(self, eventobj: Event):
        logger.applog(f"Agreed on {eventobj.eventcontent}")

    def on_timer_expired(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers["propose"] = self.on_propose
        self.eventhandlers["agree"] = self.on_agree
        self.eventhandlers["timerexpired"] = self.on_timer_expired


class AdHocNode(GenericModel):

    def on_init(self, eventobj: Event):
        #logger.applog(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj)

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        self.appl = ApplicationLayerComponent("ApplicationLayer", componentinstancenumber, topology=topology)
        self.net = GenericNetworkLayer("NetworkLayer", componentinstancenumber, topology=topology)
        self.link = GenericLinkLayer("LinkLayer", componentinstancenumber, topology=topology)
        # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

        self.components.append(self.appl)
        self.components.append(self.net)
        self.components.append(self.link)
        
        ##Connect the bottom component to the composite component....
        ## CONNECTION USING INFIX OPERATAORS
        self.appl |D| self.net 
        self.net |D| self.link
        self.link |D| self
        
        self |U| self.link 
        self.link |U| self.net
        self.net |U| self.appl 

        ## CONNECTION using U (up) D (down) P (peer) functions

        # self.appl.D(self.net)
        # self.net.D(self.link)
        # self.link.D(self)

        # self.U(self.link)
        # self.link.U(self.net)
        # self.net.U(self.appl)
        
        ## CONNECTION USING direct function    
        # self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.net)
        # self.net.connect_me_to_component(ConnectorTypes.UP, self.appl)
        # self.net.connect_me_to_component(ConnectorTypes.DOWN, self.link)
        # self.link.connect_me_to_component(ConnectorTypes.UP, self.net)
        # self.link.connect_me_to_component(ConnectorTypes.DOWN, self)
        # self.connect_me_to_component(ConnectorTypes.UP, self.link)


def main():
    #NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
    setAHCLogLevel(25)
    setAHCLogLevel(DEBUG_LEVEL_APPLOG)
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    #G = nx.random_geometric_graph(4, 0.1)
    G =nx.Graph()
    G.add_node(0)
    G.add_node(1)
    G.add_node(2)
    G.add_edge(0,1)
    G.add_edge(1,0)
    G.add_edge(0,2)
    G.add_edge(2,0)
    G.add_edge(1,2)
    G.add_edge(2,1)
    
    #nx.draw(G, with_labels=True, font_weight='bold')
    #plt.draw()
    # logger.debug("debug")
    # logger.info("info")
    # logger.warning("warning")
    # logger.error("error")
    # logger.critical("critical")
    topo = Topology()
    topo.construct_from_graph(G, AdHocNode, GenericChannel)
    
    topo.start()
    
    #plt.show()  # while (True): pass
    time.sleep(1)
    logger.applog(str(topo))
    topo.exit()

if __name__ == "__main__":
    main()
