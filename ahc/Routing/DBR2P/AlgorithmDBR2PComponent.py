import queue
import threading
import time

from ahc.Ahc import ComponentModel, Event,  EventTypes, GenericMessage
from ahc.Routing.DBR2P.Messages import DBR2PMessageHeader, DBR2PMessagePayload, DBR2PMesageType

TIME_TO_WAIT = 2.0  # This is time out in sec for  SOURCE_NODE_ROUTE_DISCOVERY and DESTINATION_RECEIVE_request
Tc_TO_WAIT = 2.0  # This is time to wait in sec to get another RD_request from the same source for intermediate_node_receive_RDrequest
N = 3  # This is for RECEIVE_RD-request to check number of time #RD received


# TOSEC = 1000.0
# TOMS = 1000.0

class RoutingDBR2PComponent(ComponentModel):

    def __init__(self, componentname, componentid):
        super(RoutingDBR2PComponent, self).__init__(componentname, componentid)
        self.SequenceNumber = 1
        self.RDRequestCache = {}  # Key Sequence  Value n For intermediate_node_receive_RDrequest
        self.BackupRouteCache = {}  # Key (Source-Destination) Value Route
        self.TimersIntermediate = {}  # Key Source ID Value Time
        self.TimersDestination = {}  # Key Source ID Value Time
        self.RouteDiscoveryThreads = {}  # key Destination value Condition To Use later on Event to notify Thread
        self.DestinationReceiverThreads = {}  # key Source value Condition To Use later on Event to notify Thread
        self.RDReplies = {}  # key Destination value message for source_node_route_discovery
        self.RDRequests = {}  # key Source value message Queue This is only to put RDRequest if this node is the Destination for threading purposes
        self.LinkMaintenanceThreads = {}  # key (source-destination) Value condition
        self.DTPackets = {}  # key (Source-Destination) Value Queue

    def on_message_from_bottom(self, eventobj: Event):
        # print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.interfaceid} & {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")
        if eventobj.eventcontent.header.messagetype == DBR2PMesageType.DT:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
                self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
            elif self.componentinstancenumber in eventobj.eventcontent.payload.messagepayload:
                key = (eventobj.eventcontent.header.messagefrom, eventobj.eventcontent.header.messageto)
                try:
                    condition = self.LinkMaintenanceThreads[key]
                    condition.acquire()
                    self.DTPackets[key].put(eventobj)
                    condition.notify()
                    condition.release()
                except KeyError:
                    condition = threading.Condition()
                    self.LinkMaintenanceThreads[key] = condition
                    self.DTPackets[key] = queue.Queue()
                    args = (eventobj, condition)
                    thread = threading.Thread(target=self.link_maintenance, args=args)
                    thread.start()
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.RDRequest:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                try:
                    condition = self.DestinationReceiverThreads[eventobj.eventcontent.header.messagefrom]
                    condition.acquire()
                    self.RDRequests[eventobj.eventcontent.header.messagefrom].put(eventobj)
                    condition.notify()
                    condition.release()
                except KeyError:
                    if eventobj.eventcontent.header.messagefrom in self.TimersDestination.keys():
                        if time.time() - self.TimersDestination[eventobj.eventcontent.header.messagefrom] < Tc_TO_WAIT:
                            return  # Discard
                        else:
                            self.TimersDestination.pop(eventobj.eventcontent.header.messagefrom)
                    condition = threading.Condition()
                    self.DestinationReceiverThreads[eventobj.eventcontent.header.messagefrom] = condition
                    self.RDRequests[eventobj.eventcontent.header.messagefrom] = queue.Queue()
                    args = (eventobj, eventobj.eventcontent.header.sequencenumber, condition)
                    thread = threading.Thread(target=self.destination_receive_RDrequest, args=args)
                    thread.start()
            else:
                self.intermediate_node_receive_RDrequest(eventobj)

        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.LFM:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                self.link_fail(eventobj)
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.LRM:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                self.send_up(eventobj)
            elif self.componentinstancenumber in eventobj.eventcontent.payload.messagepayload:
                if self.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[-1]:
                    return  # discard
                #  It came in upstream
                if eventobj.eventsource.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[
                    eventobj.eventcontent.payload.messagepayload.index(self.componentinstancenumber) + 1]:
                    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.RDReply:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                try:
                    condition = self.RouteDiscoveryThreads[eventobj.eventcontent.header.messagefrom]
                    condition.acquire()
                    self.RDReplies[eventobj.eventcontent.header.messagefrom] = eventobj
                    condition.notify()
                    condition.release()
                except KeyError:
                    # print(f"Time ot route discovery {self.componentinstancenumber}")
                    return  # Discard
            elif self.componentinstancenumber in eventobj.eventcontent.payload.messagepayload:
                if self.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[-1]:
                    return  # discard
                #  It came in upstream
                if eventobj.eventsource.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[
                    eventobj.eventcontent.payload.messagepayload.index(self.componentinstancenumber) + 1]:
                    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.BSP:
            if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
                self.receive_BSpacket(eventobj)
            elif self.componentinstancenumber in eventobj.eventcontent.payload.messagepayload:
                if self.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[-1]:
                    return  # discard
                #  It came in upstream
                if eventobj.eventsource.componentinstancenumber == eventobj.eventcontent.payload.messagepayload[
                    eventobj.eventcontent.payload.messagepayload.index(self.componentinstancenumber) + 1]:
                    # print(f"M {self.componentinstancenumber}: {eventobj.eventsource.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} S {eventobj.eventcontent.header.messagefrom} T {eventobj.eventcontent.header.messageto} R : {eventobj.eventcontent.payload.messagepayload}")
                    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
        else:
            pass  # discard event

    def on_message_from_top(self, eventobj: Event):
        # print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")
        if eventobj.eventcontent.header.messagetype == DBR2PMesageType.RDRequest:
            if eventobj.eventcontent.header.messageto in self.RouteDiscoveryThreads.keys():
                return  # discard event it should not happen though
            condition = threading.Condition()
            eventobj.eventcontent.header.sequencenumber = self.SequenceNumber
            self.SequenceNumber += 1
            self.RouteDiscoveryThreads[eventobj.eventcontent.header.messageto] = condition
            args = (eventobj, condition)
            source_node_route_discovery_thread = threading.Thread(target=self.source_node_route_discovery, args=args)
            source_node_route_discovery_thread.start()
        elif eventobj.eventcontent.header.messagetype == DBR2PMesageType.DT:
            key = (eventobj.eventcontent.header.messagefrom, eventobj.eventcontent.header.messageto)
            try:
                condition = self.LinkMaintenanceThreads[key]
                condition.acquire()
                self.DTPackets[key].put(eventobj)
                condition.notify()
                condition.release()
            except KeyError:
                condition = threading.Condition()
                self.LinkMaintenanceThreads[key] = condition
                self.DTPackets[key] = queue.Queue()
                args = (eventobj, condition)
                thread = threading.Thread(target=self.link_maintenance, args=args)
                thread.start()
        else:
            self.send_down(eventobj)

    # This is thread routine since it is blocking op
    def source_node_route_discovery(self, eventobj: Event, condition: threading.Condition):
        # print(f"source_node_route_discovery:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")

        # start timer
        # create RD request
        # broadcast RD request
        # Wait for id Reply or Time out
        # if RD reply received return the route
        # else return ERROR

        condition.acquire()
        eventobj.eventcontent.payload.messagepayload.append(self.componentinstancenumber)
        eventobj.eventcontent.payload.time = time.time()
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
        value = condition.wait(TIME_TO_WAIT)  # Wait for RD reply ot time out like while
        if value:
            # Send RD Reply to App

            event = self.RDReplies.pop(eventobj.eventcontent.header.messageto)

            event.event = EventTypes.MFRB
            self.send_up(Event(self, EventTypes.MFRB, event.eventcontent))

        else:

            # return ERROR to App
            error_header = DBR2PMessageHeader(DBR2PMesageType.ERROR, eventobj.eventcontent.header.messagefrom,
                                              eventobj.eventcontent.header.messageto,
                                              sequencenumber=eventobj.eventcontent.header.sequencenumber)
            payload = eventobj.eventcontent.payload
            payload.messagepayload = []
            self.send_up(Event(self, EventTypes.MFRB, GenericMessage(error_header, payload)))

        # remove condition from Dictionary
        self.RouteDiscoveryThreads.pop(eventobj.eventcontent.header.messageto)
        condition.release()
    def intermediate_node_receive_RDrequest(self, eventobj: Event):
        # print(f"intermediate_node_receive_RDrequest:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")

        sequence_number = eventobj.eventcontent.header.sequencenumber
        source = eventobj.eventcontent.header.messagefrom
        if self.is_RDRequest_recevied_first_time(sequence_number) and not self.check_if_in_RDrequest(eventobj):
            self.RDRequestCache[sequence_number] = 1
            self.TimersIntermediate[source] = time.time()  # Start timer
            eventobj.eventcontent.payload.messagepayload.append(self.componentinstancenumber)
            self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
        else:
            if self.check_if_in_RDrequest(eventobj):
                return
            elif self.RDRequestCache[sequence_number] >= N or (
                    time.time() - self.TimersIntermediate[source] <= Tc_TO_WAIT) if (
                    # Discard request if it is from the same source within the time interval
                    source in self.TimersIntermediate.keys()) else False:
                return
            else:
                # This is not in Paper but it must be
                self.TimersIntermediate[source] = time.time()
                # end
                self.RDRequestCache[sequence_number] += 1
                eventobj.eventcontent.payload.messagepayload.append(self.componentinstancenumber)
                self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
                return

    # This is thread routine since it is blocking op
    def destination_receive_RDrequest(self, eventobj: Event, sequence_number, condition: threading.Condition):
        # print(f"destination_receive_RDrequest:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")

        # set timer
        # send first route to source
        # while not time out
        # receive more RD reqeust from source
        # if time out backup_node_setup
        eventobj.eventcontent.payload.messagepayload.append(self.componentinstancenumber)
        # print(f"route : {eventobj.eventcontent.payload.messagepayload}")
        Routes = [eventobj.eventcontent.payload.messagepayload]
        start_time = time.time()
        header = DBR2PMessageHeader(DBR2PMesageType.RDReply, self.componentinstancenumber,
                                    eventobj.eventcontent.header.messagefrom, sequencenumber=sequence_number)
        payload = eventobj.eventcontent.payload
        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))
        # A little change at algo
        # take end send reply for the first RDrequest
        # Then start to wait for other

        value = True
        while value:
            condition.acquire()
            time_to_wait = TIME_TO_WAIT - (time.time() - start_time)
            # print( f"Time to wait receiver : {time_to_wait}")
            if time_to_wait > 0:
                value = condition.wait(time_to_wait)  # Wait for TIME sec
            else:
                value = False
            if value:

                event_queue = self.RDRequests[eventobj.eventcontent.header.messagefrom]
                while not event_queue.empty():
                    event = event_queue.get()
                    event.eventcontent.payload.messagepayload.append(self.componentinstancenumber)
                    # print(f"route backup: {event.eventcontent.payload.messagepayload}")
                    Routes.append(event.eventcontent.payload.messagepayload)

            condition.release()

        time_to_wait = TIME_TO_WAIT - (time.time() - start_time)
        # print(f"Time to wait receiver : {time_to_wait}")
        # Remove condition var and Queue
        condition.acquire()
        self.TimersDestination[eventobj.eventcontent.header.messagefrom] = time.time()
        self.RDRequests.pop(eventobj.eventcontent.header.messagefrom)
        self.DestinationReceiverThreads.pop(eventobj.eventcontent.header.messagefrom)
        condition.release()
        # Start BackUp_Node_Setup
        self.backup_node_setup(sequence_number, Routes)
        pass

    def backup_node_setup(self, sequence_number, Routes: list):
        Backup = self.find_backup_node(Routes)
        self.setup_backup(Backup, sequence_number)

    def find_backup_node(self, Routes: list):
        Backup = {}  # key node id Value List of Routes
        for routetmp1 in Routes[:-1]:
            for routetmp2 in Routes[1:]:
                route1 = routetmp1
                route2 = routetmp2
                flag1 = 0
                flag2_start = 0
                length_of_route1 = len(route1)
                length_of_route2 = len(route2)
                while flag1 < length_of_route1:
                    flag2 = flag2_start
                    while flag2 < length_of_route2:
                        if route1[flag1] == route2[flag2]:
                            while flag1 < length_of_route1 or flag2 < length_of_route2:
                                if route1[flag1] == route2[flag2]:
                                    flag1 += 1
                                    flag2 += 1
                                else:
                                    break
                            if (0 < flag1 < length_of_route1) and (0 < flag2 < length_of_route2):
                                bakcup_node_temp = route1[flag1 - 1]
                                bakcup_route_temp = route1[flag1 - 1:]
                                if bakcup_route_temp not in Backup.values():
                                    if bakcup_node_temp not in Backup:
                                        Backup[bakcup_node_temp] = []
                                    if bakcup_route_temp not in Backup[bakcup_node_temp]:
                                        bakcup_route_temp.insert(0,routetmp1[0])
                                        Backup[bakcup_node_temp].append(bakcup_route_temp)
                                bakcup_node_temp = route2[flag2 - 1]
                                bakcup_route_temp = route2[flag2 - 1:]
                                if bakcup_route_temp not in Backup.values():
                                    if bakcup_node_temp not in Backup:
                                        Backup[bakcup_node_temp] = []
                                    if bakcup_route_temp not in Backup[bakcup_node_temp]:
                                        bakcup_route_temp.insert(0, routetmp1[0])
                                        Backup[bakcup_node_temp].append(bakcup_route_temp)
                            flag2_start = flag2
                            flag2 -= 1
                        flag2 += 1
                    flag1 += 1
        return Backup

    def setup_backup(self, BackUp: dict, sequence_number):
        for backupnode in BackUp.keys():
            for backuproute in BackUp[backupnode][1:]:
                header = DBR2PMessageHeader(DBR2PMesageType.BSP, self.componentinstancenumber, backupnode,
                                            sequencenumber=sequence_number)
                payload = DBR2PMessagePayload(backuproute)

                evt = Event(self, EventTypes.MFRT, GenericMessage(header, payload))
                # print(f"send backup:  {self.componentname}.{self.componentinstancenumber} => {evt.eventcontent.header.messagetype} {evt.eventcontent.header.messagefrom} $ {evt.eventcontent.header.messageto} R {evt.eventcontent.payload.messagepayload}")

                self.send_down(evt)

    def receive_BSpacket(self, eventobj: Event):
        # print(
        #     f"BSPacket:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto} BR :{eventobj.eventcontent.payload.messagepayload}")

        key = (eventobj.eventcontent.payload.messagepayload[0], eventobj.eventcontent.header.messagefrom)
        backup_route = eventobj.eventcontent.payload.messagepayload[1:]
        try:
            if eventobj.eventcontent.payload.messagepayload not in self.BackupRouteCache[key]:
                self.BackupRouteCache[key].append(backup_route)
        except KeyError:
            self.BackupRouteCache[key] = [backup_route]

    # It is a thread routine since it blocking op
    def link_maintenance(self, eventobj: Event, condition: threading.Condition):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        times = []
        times.append(time.time())
        self.send_down(evt)
        value = True
        key = (eventobj.eventcontent.header.messagefrom, eventobj.eventcontent.header.messageto)

        while value:
            condition.acquire()
            try:
                time_to_wait = TIME_TO_WAIT - (time.time() - times[0])
            except:
                time_to_wait = TIME_TO_WAIT
            if time_to_wait > 0:
                value = condition.wait(time_to_wait)  # Wait for
            else:
                value = False

            if not value and len(times) != 0:
                eventobj.eventcontent.header.messagetype = DBR2PMesageType.LFM
                eventobj.eventcontent.payload.time = time.time()
                self.link_fail(eventobj)
            else:
                # check if it is a new item then set timer for next one and pre
                # if it is for this one close the thread
                evt: Event

                while not self.DTPackets[key].empty():
                    evt = self.DTPackets[key].get()
                    if evt.eventcontent.payload.messagepayload[evt.eventcontent.payload.messagepayload.index(
                            self.componentinstancenumber) + 1] == evt.eventsource.componentinstancenumber:
                        try:
                            times.pop(0)
                        except:
                            pass
                    else:
                        if self.componentinstancenumber == evt.eventcontent.header.messagefrom:
                            new_evt = Event(self, EventTypes.MFRT, evt.eventcontent)
                            times.append(time.time())
                            self.send_down(new_evt)
                        elif evt.eventcontent.payload.messagepayload[evt.eventcontent.payload.messagepayload.index(
                                self.componentinstancenumber) - 1] == evt.eventsource.componentinstancenumber:
                            new_evt = Event(self, EventTypes.MFRT, evt.eventcontent)
                            times.append(time.time())
                            self.send_down(new_evt)
                condition.release()

        condition.acquire()
        self.LinkMaintenanceThreads.pop(key)
        self.DTPackets.pop(key)
        condition.release()

    def link_fail(self, eventobj: Event):
        # print(
        #     f"link_fail:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto}")

        key = (eventobj.eventcontent.payload.messagepayload[0], eventobj.eventcontent.payload.messagepayload[-1])

        if key in self.BackupRouteCache.keys():
            backup_route = self.BackupRouteCache[key].pop(0)
            if not self.BackupRouteCache[key]:  # if no Backup Route remove
                self.BackupRouteCache.pop(key)
            header = DBR2PMessageHeader(DBR2PMesageType.LRM, self.componentinstancenumber,
                                        eventobj.eventcontent.payload.messagepayload[0],
                                        sequencenumber=eventobj.eventcontent.header.sequencenumber)
            messagepayload = DBR2PMessagePayload(eventobj.eventcontent.payload.messagepayload[
                                                 :eventobj.eventcontent.payload.messagepayload.index(
                                                     backup_route[0])] + backup_route)
            messagepayload.time = time.time()
            # if this is source turn data and route to app
            # print(
            #     f"BackROute:  {self.componentname}.{self.componentinstancenumber} => {eventobj.eventcontent.header.messagetype} {eventobj.eventcontent.header.messagefrom} $ {eventobj.eventcontent.header.messageto} R: {messagepayload}")

            if eventobj.eventcontent.payload.messagepayload[0] == self.componentinstancenumber:
                self.send_up(Event(self, EventTypes.MFRB, GenericMessage(header, messagepayload)))
            else:
                # if not send to source
                self.send_down(Event(self, EventTypes.MFRT, GenericMessage(header, messagepayload)))

        elif eventobj.eventcontent.payload.messagepayload[0] == self.componentinstancenumber:
            if eventobj.eventcontent.header.messageto in self.RouteDiscoveryThreads.keys():
                return  # discard event
            condition = threading.Condition()
            dest = eventobj.eventcontent.payload.messagepayload[-1]
            if dest not in self.RouteDiscoveryThreads.keys():
                header = DBR2PMessageHeader(DBR2PMesageType.RDRequest, self.componentinstancenumber, dest, sequencenumber=self.SequenceNumber)
                payload = DBR2PMessagePayload([])
                self.SequenceNumber += 1
                self.RouteDiscoveryThreads[dest] = condition
                args = (Event(self, EventTypes.MFRT, GenericMessage(header, payload)), condition)
                source_node_route_discovery_thread = threading.Thread(target=self.source_node_route_discovery, args=args)
                source_node_route_discovery_thread.start()
        else:
            header = DBR2PMessageHeader(DBR2PMesageType.LFM, self.componentinstancenumber,
                                        eventobj.eventcontent.payload.messagepayload[
                                            eventobj.eventcontent.payload.messagepayload.index(
                                                self.componentinstancenumber) - 1],
                                        sequencenumber=eventobj.eventcontent.header.sequencenumber)
            self.send_down(Event(self, EventTypes.MFRT, GenericMessage(header, eventobj.eventcontent.payload)))

    def is_RDRequest_recevied_first_time(self, sequence_number):
        if sequence_number in self.RDRequestCache.keys():
            return False
        else:
            return True

    def RDRequest_received_time_check(self, sequence_number):
        if self.RDRequests[sequence_number] < N:
            self.RDRequests[sequence_number] += 1
            return True
        else:
            return False

    def check_if_in_RDrequest(self, evenyobj: Event):
        if self.componentinstancenumber in evenyobj.eventcontent.payload.messagepayload:
            return True
        else:
            return False
