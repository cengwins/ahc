from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology
import time
import numpy as np

class FredericksonAlgorithmAdvancedComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(FredericksonAlgorithmAdvancedComponent, self).__init__(componentname, componentid)
        self.queue_lock = Lock()
        self.message_queue = []
        self.l_parameter = 1
        if self.componentinstancenumber == 0:
            self.is_initiator = True
        else:
            self.is_initiator = False

    def on_init(self, eventobj: Event):
        super(FredericksonAlgorithmAdvancedComponent, self).on_init(eventobj)
        if not self.is_initiator:
            thread = Thread(target=self.job, args=[45, 54, 123])
            thread.start()

    def on_message_from_bottom(self, eventobj: Event):
        message_destination = eventobj.eventcontent.header.messageto.split("-")[0]
        print(f"{self.componentinstancenumber} received {message_destination}")
        if message_destination == FredericksonAlgorithmAdvancedComponent.__name__: # process only the messages targeted to this component...
            message_source_id = eventobj.eventcontent.header.messagefrom.split("-")[1]
            message_type = eventobj.eventcontent.header.messagetype
            content = eventobj.eventcontent.payload
            if message_type == "EXPLORE" or message_type == "FORWARD" or message_type=="REVERSE":
                self.queue_lock.acquire() # protect message_queue, both component thread and Toueg thread are trying to access data
                self.message_queue.append((int(message_source_id), message_type, content))
                self.queue_lock.release()

    def on_message_from_peer(self, eventobj: Event):
        message_header = eventobj.eventcontent.header
        message_target = eventobj.eventcontent.header.messageto.split("-")[0]
        if message_target == FredericksonAlgorithmAdvancedComponent.__name__:
            if self.is_initiator:
                if message_header.messagetype == "INITIATEBFSCONSTRUCTION":
                    thread = Thread(target=self.job, args=[45, 54, 123])
                    thread.start()

    def job(self, *arg):
        self.neighbors = Topology().get_neighbors(self.componentinstancenumber)  # retrieve all neighbor ids...
        self.neighbor_weights = {a: 1 for a in self.neighbors}  # for the time being each edge weight is 1...
        if self.componentinstancenumber == 0:
            self.is_initiator = True
        else:
            self.is_initiator = False

        tree = self.FredericksonAlgorithmAdvanced()
        def getPaths(data):
            if len(data) == 0:
                return [[]]
            if len(data) == 1:
                ret = getPaths(data[list(data.keys())[0]])
                for i in ret:
                    i.insert(0, list(data.keys())[0])
                return ret
            if len(data) > 1:
                ret = getPaths(data[list(data.keys())[0]])
                for kl in range(len(ret)):
                    ret[kl].insert(0, list(data.keys())[0])

                return ret + getPaths({a: data[a] for a in list(data.keys()) if a != list(data.keys())[0]})

        message_payload= getPaths(tree)

        message_header = GenericMessageHeader("BFSTREECONSTRUCTED",
                                              self.componentname + "-" + str(self.componentinstancenumber),
                                              "Coordinator-" + str(self.componentinstancenumber))
        message = GenericMessage(message_header, message_payload)
        event = Event(self, EventTypes.MFRP, message)
        self.send_peer(event)
        print("Info sent to Coordinator")

    def FredericksonAlgorithmAdvanced(self):
        self.process_id = self.componentinstancenumber
        self.positively_responded_nodes = []

        self.level_u = np.inf
        self.neighbor_level_u = {}
        self.parent_u = None
        self.children_u = {}
        self.expectedreplies = {}
        for neighbor in self.neighbors:
            self.neighbor_level_u[neighbor] = np.inf
            self.expectedreplies[neighbor] = 0

        bvalue_u = False
        sendreverse_u = True

        if self.is_initiator:
            self.level_u = 0
            k = 0
            for n in self.neighbors:
                if not n in self.children_u:
                    self.children_u[n] = []
                self.sendMessageToNeighbor(n, "EXPLORE", (k + 1, self.l_parameter))
                self.expectedreplies[n] = 1

        while True:
            new_message = self.waitNewMessage()
            sender, message_type, f = new_message
            search_depth = f

            if message_type == "FORWARD":
                bvalue_u = False
                for n in self.neighbors:
                    self.expectedreplies[n] = 0
                if self.level_u < f:
                    message_count = 0
                    for c in self.positively_responded_nodes:  # list(set(self.children_u)):
                        self.sendMessageToNeighbor(c, "FORWARD", f)
                        self.expectedreplies[c] = 1
                        message_count += 1
                    self.positively_responded_nodes = []


                if self.level_u == f:
                    message_count = 0
                    for n in self.neighbors:
                        if self.neighbor_level_u[n] != f - 1:
                            self.sendMessageToNeighbor(n, "EXPLORE", (f + 1, self.l_parameter))
                            self.expectedreplies[n] = 1
                            message_count += 1
                    if message_count == 0:
                        self.message_queue.append((-1, "REVERSE", (False, self.children_u)))
                        print(f"**********{self.process_id} sends loop back itsel... ")

            elif message_type == "EXPLORE":
                f = search_depth[0]
                m = search_depth[1]

                if self.neighbor_level_u[sender] != f - 1:
                    self.neighbor_level_u[sender] = f - 1

                if self.level_u > f:
                    bvalue_u = True
                    if not sendreverse_u:
                        self.sendMessageToNeighbor(self.parent_u, "REVERSE", (False, self.children_u))
                        sendreverse_u = True

                    self.parent_u = sender
                    self.level_u = f

                    self.children_u = {}
                    if m > 1:
                        sendreverse_u = False
                        message_count = 0
                        for n in self.neighbors:
                            if n != self.parent_u:
                                self.sendMessageToNeighbor(n, "EXPLORE", (f + 1, m - 1))
                                self.expectedreplies[n] += 1
                                message_count += 1

                    else:
                        self.sendMessageToNeighbor(sender, "REVERSE", (True, self.children_u))
                elif self.level_u == f or self.level_u == f - 1:
                    if sender in self.children_u:
                        del self.children_u[sender]
                    if sender in self.positively_responded_nodes:
                        self.positively_responded_nodes.remove(sender)

                    self.sendMessageToNeighbor(sender, "REVERSE", (False, self.children_u))
                elif self.level_u < f - 1:
                    self.sendMessageToNeighbor(sender, "REVERSE", (False, self.children_u))

            elif message_type == "REVERSE":
                b = f[0]
                if sender in self.expectedreplies:
                    self.expectedreplies[sender] -= 1
                if sender in self.neighbor_level_u and self.neighbor_level_u[sender] <= self.level_u:
                    b = False
                if b == True:
                    if sender not in self.positively_responded_nodes:
                        self.positively_responded_nodes.append(sender)
                    if self.process_id != sender:
                        self.children_u[sender] = f[1]
                    bvalue_u = True

                all_responded = True
                for i in self.expectedreplies:
                    if self.expectedreplies[i] != 0:
                        all_responded = False
                        break

                if all_responded == True:
                    if self.parent_u != None:
                        self.sendMessageToNeighbor(self.parent_u, "REVERSE", (bvalue_u, self.children_u))
                        sendreverse_u = False
                    elif bvalue_u == True:
                        bvalue_u = False
                        k = k + 1
                        message_count = 0
                        for c in self.positively_responded_nodes:  # list(set(self.children_u)):
                            self.sendMessageToNeighbor(c, "FORWARD", k)
                            self.expectedreplies[c] = 1
                            message_count += 1
                        self.positively_responded_nodes = []

                        if message_count == 0:
                            print("BFS Completed....")
                            print(f"**********{self.process_id} has problem {new_message}")
                            print(self.children_u)
                            break
                    else:
                        print("BFS Completed....")
                        break

        print(self.children_u)
        return {self.componentinstancenumber: self.children_u}

    def sendMessageToNeighbor(self, neighbor_id, message_type, message):
        print(f"{self.componentinstancenumber} sends {message_type} message to neighbor {neighbor_id}")
        message_header = GenericMessageHeader(message_type, FredericksonAlgorithmAdvancedComponent.__name__+"-"+str(self.componentinstancenumber),
        FredericksonAlgorithmAdvancedComponent.__name__+"-"+str(neighbor_id), interfaceid=str(self.componentinstancenumber)+"-"+str(neighbor_id))
        mess_ = GenericMessage(message_header, message)

        event = Event(self, EventTypes.MFRT, mess_)
        self.send_down(event)

    def waitNewMessage(self):
        self.queue_lock.acquire()
        if len(self.message_queue) > 0:
            message = self.message_queue.pop()
            sender = message[0]
            message_type = message[1]
            last_part = message[2]
            self.queue_lock.release()
            return (sender, message_type, last_part)
        else:
            self.queue_lock.release()
            return None, None, None