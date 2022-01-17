from ahc.Ahc import ComponentModel, Event, ConnectorTypes, EventTypes, Topology
from ahc.Routing.DBR2P.AlgorithmDBR2PComponent import *
from ahc.Routing.DBR2P.Messages import *
from ahc.Routing.DBR2P.ApplicationComponent import *


# Encapsulator for the DBR2P Node
class DBR2PNode(ComponentModel):
    def __init__(self, componentname, componentid):
        super(DBR2PNode, self).__init__(componentname, componentid)
        self.ApplicationComponent = ApplicationComponent(ApplicationComponent.__name__, componentid)
        self.DBR2PAlgorithmComponent = RoutingDBR2PComponent(RoutingDBR2PComponent.__name__, componentid)

        self.inactive = False

        self.ApplicationComponent.connect_me_to_component(ConnectorTypes.DOWN, self.DBR2PAlgorithmComponent)
        self.DBR2PAlgorithmComponent.connect_me_to_component(ConnectorTypes.UP, self.ApplicationComponent)

        self.connect_me_to_component(ConnectorTypes.UP, self.DBR2PAlgorithmComponent)
        self.DBR2PAlgorithmComponent.connect_me_to_component(ConnectorTypes.DOWN, self)

        self.connect_me_to_component(ConnectorTypes.PEER, self.ApplicationComponent)

    def on_message_from_bottom(self, eventobj: Event):
        #print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} & {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")
        if not self.inactive:
            self.send_up(eventobj)  # send incoming messages to upper components
        else:
            self.time_to_wait -= (time.time() - self.time_wait_start)
            if self.time_to_wait <= 0:
                self.inactive = False

    def on_message_from_top(self, eventobj: Event):
        #print(f"{EventTypes.MFRT} {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} & {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")

        if not self.inactive:
            self.send_down(eventobj)  # send incoming messages from upper components to a channel
        else:
            self.time_to_wait -= (time.time() - self.time_wait_start)
            if self.time_to_wait <= 0:
                self.inactive = False

    def inactive_for_time(self, time_to_wait):
        self.inactive = True
        self.time_to_wait = time_to_wait
        self.time_wait_start = time.time()

    def send_data_to(self, destination):
        if not self.inactive:
            header = DBR2PMessageHeader(DBR2PMesageType.DT, self.componentinstancenumber, destination)
            payload = DBR2PMessagePayload([])
            evt = Event(self, EventTypes.MFRP, GenericMessage(header, payload))
            self.send_peer(evt)
        else:
            self.time_to_wait -= (time.time() - self.time_wait_start)
            if self.time_to_wait <= 0:
                self.inactive = False

    def send_down(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.DOWN]:
                event.eventcontent.header.interfaceid = p.componentinstancenumber
                #print(
                #    f"{EventTypes.MFRT} {self.componentname}.{self.componentinstancenumber} => {event.eventcontent.header.interfaceid} & {event.eventcontent.header.messagefrom} $ {event.eventcontent.header.messageto}")

                header = DBR2PMessageHeader(event.eventcontent.header.messagetype,
                                            event.eventcontent.header.messagefrom,
                                            event.eventcontent.header.messageto,
                                            event.eventcontent.header.nexthop,
                                            event.eventcontent.header.interfaceid,
                                            event.eventcontent.header.sequencenumber)
                messagepayload = copy.deepcopy(event.eventcontent.payload.messagepayload)
                payload = DBR2PMessagePayload(messagepayload, time_now=event.eventcontent.payload.time)
                evt = Event(self, EventTypes.MFRT, GenericMessage(header, payload))
                p.trigger_event(evt)
        except Exception as e:
            print(e)
            pass
