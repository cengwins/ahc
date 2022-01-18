from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage
from ahc.Routing.DBR2P.Messages import *

import copy

class ApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationComponent, self).__init__(componentname, componentid)
        self.routes = {}
        self.message_arrival_times = {}
        self.message_route_discovery_times = {}
        self.message_route_discovery_from_backup_times = {}
    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == DBR2PMesageType.ERROR:
            try:
                self.routes.pop(eventobj.eventcontent.header.messageto)
            except:
                pass
            print("{ERROR:{" + f"{eventobj.eventcontent.header.messagefrom}:{eventobj.eventcontent.header.messageto}"+"}")
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.RDReply:
            delta = time.time() - eventobj.eventcontent.payload.time
            dest = eventobj.eventcontent.header.messagefrom
            try:
                self.message_route_discovery_times[dest].append(delta)
            except KeyError:
                self.message_route_discovery_times[dest] = [delta]
            self.routes[dest] = eventobj.eventcontent.payload.messagepayload
            print("{"+f"RouteDiscovered:{time.time() - eventobj.eventcontent.payload.time},"+"{"+f"Route:{eventobj.eventcontent.payload.messagepayload}"+"}"+"}")
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.DT:
            delta = time.time() - eventobj.eventcontent.payload.time
            try:
                self.message_arrival_times[eventobj.eventcontent.header.messagefrom].append(delta)
            except KeyError:
                self.message_arrival_times[eventobj.eventcontent.header.messagefrom] = [delta]
            #print("{"+f"MessageReceived:{time.time() -eventobj.eventcontent.payload.time}"+"}")
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.LRM:
            delta = time.time() - eventobj.eventcontent.payload.time
            dest = eventobj.eventcontent.payload.messagepayload[-1]
            try:
                self.message_route_discovery_from_backup_times[dest].append(delta)
            except KeyError:
                self.message_route_discovery_from_backup_times[dest] = [delta]
            self.routes[dest] = eventobj.eventcontent.payload.messagepayload
            print("{" + f"RouteDiscoveredFromBackup:{time.time() - eventobj.eventcontent.payload.time}"+"}")
        else:
            print(f"{eventobj.eventcontent.header.messagetype}")

    def on_message_from_peer(self, eventobj: Event):
        if eventobj.eventcontent.header.messagetype == DBR2PMesageType.DT:
            try:
                route = copy.deepcopy(self.routes[eventobj.eventcontent.header.messageto])
                header = DBR2PMessageHeader(DBR2PMesageType.DT, self.componentinstancenumber, eventobj.eventcontent.header.messageto)
                payload = DBR2PMessagePayload(route)
                message = GenericMessage(header, payload)
                message.payload.time = time.time()
                self.send_down(Event(self, EventTypes.MFRT, message))
            except KeyError:
                header = DBR2PMessageHeader(DBR2PMesageType.RDRequest, self.componentinstancenumber,
                                            eventobj.eventcontent.header.messageto)
                payload = DBR2PMessagePayload([])
                message = GenericMessage(header, payload)
                message.payload.time = time.time()
                self.send_down(Event(self, EventTypes.MFRT, message))
        else:
            print(f"{eventobj.eventcontent.header.messagetype}")
