from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes

class Coordinator(ComponentModel):
    def __init__(self, componentname, componentid):
        super(Coordinator, self).__init__(componentname, componentid)
        self.RoutingTable = {}

    def on_message_from_top(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        print(f"Coordinator receives message from top {messageto}")
        if messageto == Coordinator.__name__:
            if sender == "ApplicationComponent" and message_type == "INITIATE":
                if self.componentinstancenumber == 0:
                    message_header = GenericMessageHeader("INITIATEROUTE",
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "TouegRoutingComponent-" + str(self.componentinstancenumber))
                    message = GenericMessage(message_header, "")
                    kickstarter = Event(self, EventTypes.MFRP, message)
                    self.send_peer(kickstarter)
                    print("Coordinator -> Toueg")
            elif sender == "ApplicationComponent" and (message_type == "APPQUERY" or message_type == "APPRESPONSE"):
                if len(self.RoutingTable) > 0:
                    dest, info = message

                    neighbor_id = self.RoutingTable[self.componentinstancenumber][dest]
                    message_header = GenericMessageHeader(message_type, Coordinator.__name__ + "-" + str(
                        self.componentinstancenumber),
                                                          Coordinator.__name__ + "-" + str(neighbor_id),
                                                          interfaceid=str(self.componentinstancenumber) + "-" + str(
                                                              neighbor_id))
                    mess_ = GenericMessage(message_header, (dest, self.componentinstancenumber, info))

                    event = Event(self, EventTypes.MFRT, mess_)
                    self.send_down(event)
                    print(f"Coordinator {self.componentinstancenumber} sends APPQUERY {neighbor_id} to relay it {dest} - {self.RoutingTable}")


    def on_message_from_peer(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == Coordinator.__name__:
            if sender == "TouegRoutingComponent" and message_type == "ROUTINGCOMPLETED":
                self.RoutingTable = message[1]
                if self.componentinstancenumber == 0:
                    message_header = GenericMessageHeader("ROUTINGCOMPLETED",
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "ApplicationComponent-" + str(self.componentinstancenumber))
                    message = GenericMessage(message_header, self.RoutingTable)
                    kickstarter = Event(self, EventTypes.MFRB, message)
                    self.send_up(kickstarter)



    def on_init(self, eventobj: Event):
        pass
    def on_message_from_bottom(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == Coordinator.__name__:
            if sender == "Coordinator" and (message_type == "APPQUERY" or message_type == "APPRESPONSE"):
                dest, source, content = message
                print(f"Coordinator {self.componentinstancenumber} has received APPQUERY {dest, source}")

                if dest == self.componentinstancenumber:
                    message_header = GenericMessageHeader(message_type,
                                                          "Coordinator-" + str(self.componentinstancenumber),
                                                          "ApplicationComponent-" + str(self.componentinstancenumber))
                    message_ = GenericMessage(message_header, (source, content))
                    kickstarter = Event(self, EventTypes.MFRB, message_)
                    self.send_up(kickstarter)
                    # send to app layer
                    pass
                else:
                    if len(self.RoutingTable) > 0:
                        neighbor_id = self.RoutingTable[self.componentinstancenumber][dest]

                        message_header = GenericMessageHeader(message_type, Coordinator.__name__ + "-" + str(
                            self.componentinstancenumber),
                                                              Coordinator.__name__ + "-" + str(neighbor_id),
                                                              interfaceid=str(self.componentinstancenumber) + "-" + str(
                                                                  neighbor_id))
                        mess_ = GenericMessage(message_header, message)

                        event = Event(self, EventTypes.MFRT, mess_)
                        self.send_down(event)
                        print(f"*****Routing from {self.componentinstancenumber} to {neighbor_id} - {self.RoutingTable}*****")






