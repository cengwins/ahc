from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology
import time

class TouegRoutingComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(TouegRoutingComponent, self).__init__(componentname, componentid)
        # two dictionaries are indexed with the component id, hence, while broadcasting, the other nodes can easily understant whose distance information they are currently working
        self.DistanceInformation = {self.componentinstancenumber: {}} # stores the shortest path distance values
        self.ParentInformation = {self.componentinstancenumber: {}}
        self.all_process_ids = []
        self.Su = [] # processed node list, algorithm terminates when all nodes are processed...
        self.neighbors = [] # the list of neighbors (ids) connected to main node...
        self.message_queue = [] # for the next invication clear it...
        self.queue_lock = Lock()

    def on_init(self, eventobj: Event):
        super(TouegRoutingComponent, self).on_init(eventobj)
        # the first process does not start immediate, it stars with a peer message
        if self.componentinstancenumber != 0:
            thread = Thread(target=self.job, args=[45, 54, 123])
            thread.start()

    def on_message_from_bottom(self, eventobj: Event):
        message_destination = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_destination == TouegRoutingComponent.__name__: # process only the messages targeted to this component...
            message_source_id = eventobj.eventcontent.header.messagefrom.split("-")[1]
            message_type = eventobj.eventcontent.header.messagetype
            content = eventobj.eventcontent.payload

            if message_type == "INFO" or message_type == "DISTANCE":
                self.queue_lock.acquire() # protect message_queue, both component thread and Toueg thread are trying to access data
                self.message_queue.append((int(message_source_id), message_type, content))
                self.queue_lock.release()


    def on_message_from_peer(self, eventobj: Event):
        message_header = eventobj.eventcontent.header
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == "TouegRoutingComponent":
            if self.componentinstancenumber == 0:
                if message_header.messagetype == "INITIATEROUTE":
                    thread = Thread(target=self.job, args=[45, 54, 123])
                    thread.start()

    def job(self, *arg):
        self.all_process_ids = []
        for element in ComponentRegistry().components:
            if "MachineLearningNode" in element:
                parts = int(element.split("MachineLearningNode")[1])
                self.all_process_ids.append(parts)
        print("Available nodes : ", self.all_process_ids)
        self.neighbors = Topology().get_neighbors(self.componentinstancenumber) # retrieve all neighbor ids...

        self.neighbor_weights = {a: 1 for a in self.neighbors} # for the time being each edge weight is 1...

        neighbor_ids = [a for a in self.neighbors]
        # found shortest path information will be sent to Coordinator component
        message_payload = self.TOUEG(self.all_process_ids, neighbor_ids, self.neighbor_weights)
        message_header = GenericMessageHeader("ROUTINGCOMPLETED", self.componentname+"-"+str(self.componentinstancenumber),
                                              "Coordinator-"+str(self.componentinstancenumber))
        message = GenericMessage(message_header, message_payload)
        event = Event(self, EventTypes.MFRP, message)
        self.send_peer(event)


    def TOUEG(self, vertices, neigbors, neighbor_weights):
        self.process_id = self.componentinstancenumber
        self.Su = set([])
        self.ParentInformation = {self.process_id: {}}

        for v in vertices:
            if v == self.process_id:
                self.DistanceInformation[self.process_id][v] = 0
                self.ParentInformation[self.process_id][v] = v
            elif v in neigbors:
                self.DistanceInformation[self.process_id][v] = neighbor_weights[v]
                self.ParentInformation[self.process_id][v] = v;
            else:
                self.DistanceInformation[self.process_id][v] = float("inf")
                self.ParentInformation[self.process_id][v] = None

        # For pivot selection, nodes are labeled with their process id
        unordered_vertices = [a for a in vertices]
        unordered_vertices.sort()
        sorted_ids = unordered_vertices
        current_pivot_index = 0
        vertices = set(vertices)
        print(vertices.difference(self.Su))
        while len(vertices.difference(self.Su)) != 0 : # Su != Vertices should be...
            pivot = sorted_ids[current_pivot_index]
            # print(f"Process {self.process_id} picks pivot={pivot}")
            for neighbor in neigbors:
                if self.ParentInformation[self.process_id][pivot] == neighbor:
                    self.sendMessageToNeighbor(neighbor, "INFO", "Child("+str(pivot)+")")
                else:
                    self.sendMessageToNeighbor(neighbor, "INFO", "NotChild("+str(pivot)+")")
            # wait for a specific number of messages
            while True:
                t = self.getPendingChildMessageCount(pivot)
                if t != len(neigbors):
                    time.sleep(0.4)
                else:
                    break

            if self.DistanceInformation[self.process_id][pivot] < float("inf"):
                if self.process_id != pivot:

                    D_pivot = self.waitPivotDistanceFrom(self.ParentInformation[self.process_id][pivot], pivot)
                    while D_pivot is None:
                        D_pivot = self.waitPivotDistanceFrom(self.ParentInformation[self.process_id][pivot], pivot)

                    for neighbor in neigbors:
                        if self.getParticularChildMessage(neighbor, pivot):
                            self.sendMessageToNeighbor(neighbor, "DISTANCE", (pivot, D_pivot))
                    for vertex in vertices:
                        if self.DistanceInformation[self.process_id][vertex] > self.DistanceInformation[self.process_id][pivot] + D_pivot[pivot][vertex]:
                            self.DistanceInformation[self.process_id][vertex] = self.DistanceInformation[self.process_id][pivot]+D_pivot[pivot][vertex]
                            self.ParentInformation[self.process_id][vertex] = self.ParentInformation[self.process_id][pivot]
                elif self.process_id == pivot:
                    received_child_messages = []
                    for neighbor in neigbors:
                        if self.getParticularChildMessage(neighbor, pivot):
                            received_child_messages.append(neighbor)
                    for neighbor in received_child_messages:
                        self.sendMessageToNeighbor(neighbor, "DISTANCE", (pivot, self.DistanceInformation))

            self.Su.add(pivot)
            current_pivot_index += 1
        print(f"\n\nPath Finding has been completed {self.process_id} - {self.DistanceInformation} - {self.ParentInformation}")
        return (self.DistanceInformation, self.ParentInformation)


    def sendMessageToNeighbor(self, neighbor_id, message_type, message):
        message_header = GenericMessageHeader(message_type, TouegRoutingComponent.__name__+"-"+str(self.componentinstancenumber),
        TouegRoutingComponent.__name__+"-"+str(neighbor_id), interfaceid=str(self.componentinstancenumber)+"-"+str(neighbor_id))
        mess_ = GenericMessage(message_header, message)

        event = Event(self, EventTypes.MFRT, mess_)
        self.send_down(event)

    def getPendingChildMessageCount(self, pivot):
        child_message_count = 0
        for i in self.message_queue:
            if i[1] == "INFO" and (("Child(" + str(pivot) + ")" == i[2]) or ("NotChild(" + str(pivot) + ")" == i[2])):
                child_message_count += 1
        return child_message_count

    def waitPivotDistanceFrom(self, source, pivot):
        self.queue_lock.acquire()
        for index, i in enumerate(self.message_queue):
            if i[0] == source and i[1] == "DISTANCE" and i[2][0] == pivot:
                data = self.message_queue.pop(index)
                self.queue_lock.release()
                return data[2][1]
        self.queue_lock.release()
        return None

    def getParticularChildMessage(self, neigh, pivot):
        self.queue_lock.acquire()
        for index, i in enumerate(self.message_queue):
            if i[0] == neigh and i[1] == "INFO" and "Child("+str(pivot)+")" == i[2]:
                data = self.message_queue.pop(index)
                self.queue_lock.release()
                return True
        self.queue_lock.release()
        return False

