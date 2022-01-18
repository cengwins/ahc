from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class Coordinator(ComponentModel):
    def __init__(self, componentname, componentid):
        super(Coordinator, self).__init__(componentname, componentid)
        self.RoutingTable = {}
        self.Response_Record = {}

    def on_message_from_top(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        print(f"Coordinator receives message from top {messageto} {message_type} {message}")
        if messageto == Coordinator.__name__:
            if sender == "ApplicationComponent" and message_type == "INITIATE":
                if self.componentinstancenumber == 0:
                    message_header = GenericMessageHeader("INITIATEBFSCONSTRUCTION",
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "FredericksonAlgorithmSimpleComponent-" + str(self.componentinstancenumber))
                    message = GenericMessage(message_header, "")
                    kickstarter = Event(self, EventTypes.MFRP, message)
                    self.send_peer(kickstarter)
                    print("Coordinator -> Frederickson")
            elif sender == "ApplicationComponent" and (message_type == "APPQUERY" or message_type == "APPRESPONSE"):
                if message_type == "APPRESPONSE" or len(self.RoutingTable) > 0:
                    dest, info = message
                    path_to_follow = None
                    for i in self.RoutingTable:
                        if dest in i:
                            path_to_follow = i
                            break
                    if message_type == "APPRESPONSE":
                        path_to_follow = self.Response_Record[dest]

                    neighbor_id = path_to_follow[1]
                    if message_type == "APPRESPONSE":
                        print("Neighbor : ", neighbor_id)


                    message_header = GenericMessageHeader(message_type, Coordinator.__name__ + "-" + str(
                        self.componentinstancenumber),
                                                          Coordinator.__name__ + "-" + str(neighbor_id),
                                                          interfaceid=str(self.componentinstancenumber) + "-" + str(
                                                              neighbor_id))
                    mess_ = GenericMessage(message_header, (path_to_follow[1:], (path_to_follow), dest, self.componentinstancenumber, info))

                    event = Event(self, EventTypes.MFRT, mess_)
                    self.send_down(event)
                    print(f"Coordinator {self.componentinstancenumber} sends APPQUERY {neighbor_id} to relay it {dest} - {self.RoutingTable}")


    def on_message_from_peer(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == Coordinator.__name__:
            if sender == "FredericksonAlgorithmSimpleComponent" and message_type == "BFSTREECONSTRUCTED":
                self.RoutingTable = message
                print(f"Coordinator {self.componentinstancenumber} has received BFS Tree {self.RoutingTable}")


    def on_init(self, eventobj: Event):
        pass
    def on_message_from_bottom(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == Coordinator.__name__:
            if sender == "Coordinator" and (message_type == "APPQUERY" or message_type == "APPRESPONSE"):
                curr_, path_to_follow, dest, source, content = message
                print(f"Coordinator {self.componentinstancenumber} has received APPQUERY {curr_, path_to_follow, dest, source}")

                if dest == self.componentinstancenumber:
                    message_header = GenericMessageHeader(message_type,
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "ApplicationComponent-" + str(self.componentinstancenumber))
                    message_ = GenericMessage(message_header, (source, content))
                    kickstarter = Event(self, EventTypes.MFRB, message_)
                    self.send_up(kickstarter)
                    self.Response_Record[source] = list(reversed(path_to_follow))
                    print(f"Response Record : ", self.Response_Record)
                    # send to app layer
                    pass
                else:
                        neighbor_id = curr_[1]

                        message_header = GenericMessageHeader(message_type, Coordinator.__name__ + "-" + str(
                            self.componentinstancenumber),
                                                              Coordinator.__name__ + "-" + str(neighbor_id),
                                                              interfaceid=str(self.componentinstancenumber) + "-" + str(
                                                                  neighbor_id))
                        mess_ = GenericMessage(message_header, (curr_[1:], path_to_follow, dest, source, content))

                        event = Event(self, EventTypes.MFRT, mess_)
                        self.send_down(event)
                        print(f"*****Routing from {self.componentinstancenumber} to {neighbor_id} - {self.RoutingTable}*****")


