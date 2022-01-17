from enum import Enum
from tabulate import tabulate

from ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessageHeader, GenericMessage, MessageDestinationIdentifiers
from threading import Timer

class DsdvTimer():

    def __init__(self):
        self.working = False

    def start(self, interval, handleFunction, args=None, kwargs=None):
        self.interval = interval
        self.handleFunction = handleFunction
        self.thread = Timer(self.interval, self.handleFunction, args, kwargs)
        self.thread.daemon = True
        self.thread.start()
        self.working = True

    def cancel(self):
        self.thread.cancel()
        self.working = False


# Definition of message types in the DSDV routing protocol
# Full Dump Update Message: Entire routing table will be send
# Incremental Update: One entry in the routing table will be send
class DsdvMessageTypes(Enum): # Control Plane message types
    fullDumpUpdate = "Full Dump Update Message"
    incrementalUpdate = "Incremental Update Message"


class DataMessageTypes(Enum):
    appData = "Application Data Message"


# Definition of the index for each column in the routing table
class RoutingTableColumn(Enum):
    destination = 0
    nextHop = 1
    metric = 2
    sequenceNumber = 3


class DsdvService(ComponentModel):

    def __init__(self, componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)    # init super class
        self.routingTable = []      # a routing table to keep minimum distance information to the other nodes
        self.sequenceNumber = 0     # sequence number of the broadcast messages for self component

        # First entry to add to self routing table is the self distance
        self.routingTable.append([componentinstancenumber, componentinstancenumber, 0, self.sequenceNumber])
        # Create a timer thread instance to send periodic update messages
        self.periodicUpdateTimer = DsdvTimer()
        # First message will be send 1 second after the init. The period will be different
        self.periodicUpdateTimer.start(1, self.send_periodic_update)
        # Create timer thread instances to be able to schedule update messages aside from the periodic update
        self.scheduleFullDumpUpdate = DsdvTimer()
        self.scheduleIncrementalUpdate = DsdvTimer()
        # Decide interval of the periodic update messages. No hard limitation
        self.periodicUpdateMessageInterval = 10

        # Added only to debug. The variables can be removed
        self.schedulePrintRoutingTable = DsdvTimer()
        self.numberOfIncrementalUpdate = 0
        self.numberOfFullDumpUpdate = 0
        self.numberOfUpdateMessage = 0
        self.printRoutingTableOnPeriodicUpdates = True
        self.printNumberOfMessagesOnPeriodicUpdates = False
        self.printNumberOfMessagesOnEveryUpdate = False

    # This function increases the self sequence number and
    # updates the routing table according to new self sequence number
    #
    def increase_self_sequence_number(self):
        # Sequence numbers should be even numbers
        self.sequenceNumber = self.sequenceNumber + 2
        # Update the routing table according to new self sequence number
        for row in self.routingTable:
            if row[RoutingTableColumn.destination.value] == self.componentinstancenumber:
                row[RoutingTableColumn.sequenceNumber.value] = self.sequenceNumber

    # This function generates a full dump update message and sends to lower layer
    # @param routingTable is the self routing table to broadcast
    #
    def send_full_dump_update(self, routingTable):
        payload = routingTable.copy()
        destination = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        header = GenericMessageHeader(DsdvMessageTypes.fullDumpUpdate, self.componentinstancenumber, destination,
                                      nexthop)

        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))
        self.increase_self_sequence_number()

        # Added to debug
        self.numberOfFullDumpUpdate = self.numberOfFullDumpUpdate + 1
        self.numberOfUpdateMessage = self.numberOfUpdateMessage + 1
        if self.printNumberOfMessagesOnEveryUpdate:
            print(self.unique_name() + " Number Of Update Message: " + str(self.numberOfUpdateMessage))

    # This function generates an incremental update message and sends to lower layer
    # @param routingTableEntry is an entry of the self routing table to broadcast
    #
    def send_incremental_update(self, routingTableEntry):
        payload = routingTableEntry.copy()
        destination = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        nexthop = MessageDestinationIdentifiers.LINKLAYERBROADCAST
        header = GenericMessageHeader(DsdvMessageTypes.incrementalUpdate, self.componentinstancenumber, destination,
                                      nexthop)

        message = GenericMessage(header, payload)
        self.send_down(Event(self, EventTypes.MFRT, message))
        self.increase_self_sequence_number()

        # Added to debug
        self.numberOfIncrementalUpdate = self.numberOfIncrementalUpdate + 1
        self.numberOfUpdateMessage = self.numberOfUpdateMessage + 1
        if self.printNumberOfMessagesOnEveryUpdate:
            print(self.unique_name() + " Number Of Update Message: " + str(self.numberOfUpdateMessage))

    # This function provides a periodic call of the send_full_dump_update() function with the help of a timer thread
    #
    def send_periodic_update(self):
        self.send_full_dump_update(self.routingTable)
        self.periodicUpdateTimer.cancel()
        self.periodicUpdateTimer.start(self.periodicUpdateMessageInterval, self.send_periodic_update)

        # added to debug purpose only
        if self.printRoutingTableOnPeriodicUpdates:
            self.schedulePrintRoutingTable.start(self.componentinstancenumber, self.print_self_routing_table)
        elif self.printNumberOfMessagesOnPeriodicUpdates:
            print(self.unique_name() + " Number Of Update Message: " + str(self.numberOfUpdateMessage))

    # This function sends full dump update message as a result of the scheduling
    #
    def send_scheduled_full_dump_update(self, routingTable):
        if self.scheduleFullDumpUpdate.working:
            self.scheduleFullDumpUpdate.cancel()
            self.send_full_dump_update(routingTable)

    # This function sends incremental update message as a result of the scheduling
    #
    def send_scheduled_incremental_update(self, routingTableEntry):
        if self.scheduleIncrementalUpdate.working:
            self.scheduleIncrementalUpdate.cancel()
            self.send_incremental_update(routingTableEntry)

    # This function schedules sending an incremental update message
    # The function invoked from processing an update message
    #
    def schedule_incremental_update(self, routingTableEntry):
        # If a full dump update message is scheduled, there is no need to schedule an incremental update since
        # the full dump update message covers the incremental update
        if self.scheduleFullDumpUpdate.working:
            pass
        else:
            # If more than 1 request exist for incremental update, schedule a full dump update instead
            if self.scheduleIncrementalUpdate.working:
                self.scheduleIncrementalUpdate.cancel()
                self.scheduleFullDumpUpdate.start(1, self.send_scheduled_full_dump_update, [self.routingTable])
            else:
                self.scheduleIncrementalUpdate.start(2, self.send_scheduled_incremental_update, [routingTableEntry])

    # This function schedules sending a full dump update message
    # The function invoked from processing an update message
    #
    def schedule_full_dump_update(self):
        if self.scheduleFullDumpUpdate.working == False:
            self.scheduleFullDumpUpdate.start(1, self.send_scheduled_full_dump_update, [self.routingTable])

    # This function gets incoming full dump update messages and process
    # Process means update self routing table according to the incoming messages
    # @param payload is the payload of the incoming message which shows the entire routing table of the one of
    # the neighbors
    # @param messageFrom shows source address of the incoming message
    #
    def process_full_dump_update_message(self, payload, messageFrom):
        updatedRows = []    # Keep record of the updated entries in the self routing table

        # Process every entry in the incoming message
        for rowInPayload in payload:
            singleEntry = rowInPayload.copy()
            # Increment the metric value by 1, since the distance information was according to my neighbor
            singleEntry[RoutingTableColumn.metric.value] = singleEntry[RoutingTableColumn.metric.value] + 1

            isRoutingTableUpdated = self.process_single_entry_in_message(singleEntry, messageFrom)
            if isRoutingTableUpdated == True:
                updatedRows.append(singleEntry)

        if len(updatedRows) > 1:   # More than 1 entry changed. Invoke to schedule full dump update message
            self.schedule_full_dump_update()
        elif len(updatedRows) == 1:    # Only 1 entry changed. Invoke to schedule incremental update message is enough
            self.schedule_incremental_update(updatedRows[0])

    # This function gets incoming incremental update messages and process
    # Process means update self routing table according to the incoming messages
    # @param payload is the payload of the incoming message which shows single entry of the routing table of the one
    # of the neighbors
    # @param messageFrom shows the source address of the incoming message
    #
    def process_incremental_update_message(self, payload, messageFrom):
        singleEntry = payload.copy()
        # Increment the metric value by 1, since the distance information was according to my neighbor
        singleEntry[RoutingTableColumn.metric.value] = singleEntry[RoutingTableColumn.metric.value] + 1
        isRoutingTableUpdated = self.process_single_entry_in_message(singleEntry, messageFrom)

        if isRoutingTableUpdated == True:
            self.schedule_incremental_update(singleEntry)

    # This function processes a single entry of the incoming update message
    # @param singleEntry is the entry to process
    # @param messageFrom shows the source address of the incoming message
    # @return if the self routing table is changed or not. Only the crucial updates considered as change
    #
    def process_single_entry_in_message(self, singleEntry, messageFrom):
        destColumnIndex = RoutingTableColumn.destination.value
        nextHopColumnIndex = RoutingTableColumn.nextHop.value
        seqNumberColumnIndex = RoutingTableColumn.sequenceNumber.value
        metricColumnIndex = RoutingTableColumn.metric.value
        crucialUpdateExist = False


        # -----Update the entry of the incoming message according to self component---
        # Next hop information will be sender of the message
        singleEntry[nextHopColumnIndex] = messageFrom
        # ------------------

        # If the entry is not about myself, continue the process
        if singleEntry[destColumnIndex] != self.componentinstancenumber:
            # Search the entry which has same destination node information in self routing table
            rowIndex = self.search_for_entry(singleEntry[destColumnIndex])

            if rowIndex == -1:  # No match in self.routing table
                self.routingTable.append(singleEntry)
                self.routingTable.sort()
                crucialUpdateExist = True

            else:
                # If the entry in the message has a bigger sequence number, update the information
                if singleEntry[seqNumberColumnIndex] > self.routingTable[rowIndex][seqNumberColumnIndex]:
                    self.routingTable[rowIndex] = singleEntry
                    crucialUpdateExist = self.decide_which_update_is_crucial(singleEntry, self.routingTable[rowIndex])
                # If the entry in the message has same sequence number, choose the lower metric value
                elif singleEntry[seqNumberColumnIndex] == self.routingTable[rowIndex][seqNumberColumnIndex]:
                    if singleEntry[metricColumnIndex] < self.routingTable[rowIndex][metricColumnIndex]:
                        self.routingTable[rowIndex] = singleEntry
                        crucialUpdateExist = self.decide_which_update_is_crucial(singleEntry,
                                                                                 self.routingTable[rowIndex])
        return crucialUpdateExist

    # This function searches for an entry in the self routing table
    # Function finds the entry which caries the information about the given destination node
    # @param destinationNode is the node to look for in the self routing table
    # @return rowIndex is the index of the row which carries the information about the given destination node
    #   - If the information is not found, return -1
    #
    def search_for_entry(self, destinationNode):
        destColumnIndex = RoutingTableColumn.destination.value
        rowIndex = 0

        for rowInSelfTable in self.routingTable:
            if rowInSelfTable[destColumnIndex] == destinationNode:
                return rowIndex
            else:
                rowIndex = rowIndex + 1

        return -1

    # If the change in the entry only the sequence number, in other words the metric and next hop
    # information is same, do not broadcast the information. No significant change
    #
    def decide_which_update_is_crucial(self, entryInMessage, entryInSelfTable):

        nextHopColumnIndex = RoutingTableColumn.nextHop.value
        metricColumnIndex = RoutingTableColumn.metric.value

        if entryInMessage[metricColumnIndex] != entryInSelfTable[metricColumnIndex] or \
                entryInMessage[nextHopColumnIndex] != entryInMessage[nextHopColumnIndex]:
            return True
        else:
            return False

    def print_self_routing_table(self):
        print("\r\n\r\n" + self.unique_name() + " Routing Table")
        print(tabulate(self.routingTable, headers=[RoutingTableColumn.destination.name, RoutingTableColumn.nextHop.name,
                                                   RoutingTableColumn.metric.name,
                                                   RoutingTableColumn.sequenceNumber.name], tablefmt='grid'))

    # This function handles the messages coming from lower layer
    # Function overrides super class function
    #
    def on_message_from_bottom(self, eventobj: Event):
        msg = eventobj.eventcontent
        hdr = msg.header
        payload = msg.payload

        #----Control Plane messages---
        if hdr.messagetype == DsdvMessageTypes.fullDumpUpdate:
            self.process_full_dump_update_message(payload, hdr.messagefrom)
        elif hdr.messagetype == DsdvMessageTypes.incrementalUpdate:
            self.process_incremental_update_message(payload, hdr.messagefrom)
        #---------------

        #------Data messages----
        elif hdr.messagetype == DataMessageTypes.appData:
            # If destination of the message is myself, send to higher layer
            if hdr.messageto == self.componentinstancenumber:
                self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
            # If destination of the message is not myself, work as a router: Decide a path and resend the message
            else:
                newMessage = self.RouteAppLayerMessage(hdr.messageto, msg.payload)
                self.send_down(Event(self, EventTypes.MFRT, newMessage))

    # This function handles the messages coming from upper layer
    # Function overrides super class function
    #
    def on_message_from_top(self, eventobj: Event):
        msg = eventobj.eventcontent
        hdr = msg.header
        newMessage = self.RouteAppLayerMessage(hdr.messageto, msg.payload)
        if(newMessage != -1):
            self.send_down(Event(self, EventTypes.MFRT, newMessage))

    # This function routes a message according to self routing table.
    # The function takes destination address and payload information and regenerates the message
    # @param destination is the destination address of the message
    # @param payload is the payload part of the message
    #
    def RouteAppLayerMessage(self, destination, payload):
        entryIndex = self.search_for_entry(destination)

        if entryIndex == -1:  # No match in self.routing table. Drop the packet
            print("I am: " + self.unique_name() + " Message is dropped")
            print(payload)
            return -1
        else:
            nexthop = self.routingTable[entryIndex][RoutingTableColumn.nextHop.value]
            header = GenericMessageHeader(DataMessageTypes.appData, self.componentinstancenumber, destination,
                                          nexthop)

            message = GenericMessage(header, payload)
            return message











