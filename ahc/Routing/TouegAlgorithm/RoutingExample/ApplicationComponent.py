from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, Thread, Lock
from timeit import default_timer as timer

# where the machine learning model is loaded... The top entity for the Node...
class ApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationComponent, self).__init__(componentname, componentid)

    def on_init(self, eventobj: Event):
        if self.componentinstancenumber == 0:
            message_header = GenericMessageHeader("INITIATE", "ApplicationComponent-"+str(self.componentinstancenumber),
                                                  "Coordinator-" + str(self.componentinstancenumber))
            message = GenericMessage(message_header, "")
            kickstarter = Event(self, EventTypes.MFRT, message)
            self.send_down(kickstarter)
            print(f"App {self.componentinstancenumber} sends an INITIATE to Coordinator")

    def on_message_from_bottom(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == "ApplicationComponent":
            if message_type == "APPQUERY":
                source, content = message
                print(f"App {self.componentinstancenumber} has received {message} from {source}")
                message_header = GenericMessageHeader("APPRESPONSE",
                                                      "ApplicationComponent-" + str(self.componentinstancenumber),
                                                      "Coordinator-" + str(self.componentinstancenumber))
                message = GenericMessage(message_header, (source, "Hellooooooooo "+content))
                kickstarter = Event(self, EventTypes.MFRT, message)
                self.send_down(kickstarter)

            elif message_type == "APPRESPONSE":
                source, content = message
                print(f"App {self.componentinstancenumber} has received APPRESPONSE {message} from {source}")
            elif message_type == "ROUTINGCOMPLETED":
                print(f"App {self.componentinstancenumber} has received RoutingTable {message}")
