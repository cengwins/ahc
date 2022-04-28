import queue
from threading import Thread
from timeit import default_timer as timer

from .Experimentation.Topology import *
from .Generics import *

class GenericModel:

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        self.topology = topology
        #print("Topology", topology)
        self.context = context
        self.configurationparameters = configurationparameters
        self.eventhandlers = {EventTypes.INIT: self.on_init, EventTypes.MFRB: self.on_message_from_bottom,
                            EventTypes.MFRT: self.on_message_from_top, EventTypes.MFRP: self.on_message_from_peer}
        # Add default handlers to all instantiated components.
        # If a component overwrites the __init__ method it has to call the super().__init__ method
        self.inputqueue = queue.Queue()
        self.componentname = componentname
        self.componentinstancenumber = componentinstancenumber
        self.num_worker_threads = num_worker_threads
        self.connectors = {}
        self.terminated = False

        for i in range(self.num_worker_threads):
            t = Thread(target=self.queue_handler, args=[self.inputqueue])
            t.daemon = True
            t.start()

        try:
            if self.connectors:
                pass
        except AttributeError:
            self.connectors = {}
            # self.connectors = ConnectorList()

        #TODO: Handle This Part
        # for i in range(self.num_worker_threads):
        #     t = Thread(target=self.queue_handler, args=[self.inputqueue])
        #     t.daemon = True
        #     t.start()

        # self.registry = ComponentRegistry()
        # self.registry.add_component(self)



    def send_down(self, event: Event):
        try:
            self.connectors[ConnectorTypes.DOWN].on_message_from_top(event)

        except Exception as e:
            raise(f"Cannot send message to Down Connector {self.componentname } -- {self.componentinstancenumber}")


    def send_up(self, event: Event):
        try:
            self.connectors[ConnectorTypes.UP].eventhandlers[EventTypes.MFRB](event)
            # for p in self.connectors[ConnectorTypes.UP]:
            #     p.trigger_event(event)
        except:
            pass

    def send_peer(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.PEER]:
                p.trigger_event(event)
        except:
            pass

    def connect_me_to_component(self, name, component):
        self.connectors[name] = component

    def on_message_from_bottom(self, eventobj: Event):
        print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_peer(self, eventobj: Event):
        print(f"{EventTypes.MFRP}  {self.componentname}.{self.componentinstancenumber}")


    def on_init(self, eventobj: Event):
        if self.componentinstancenumber == 0:
            message_header = GenericMessageHeader("INITIATE  -> ", +str(self.componentname),
                                                  "Component-" + str(self.componentinstancenumber))
            message = GenericMessage(message_header, "")
            kickstarter = Event(self, EventTypes.MFRT, message)
            self.send_down(kickstarter)
            print(f"{self.componentname} - {self.componentinstancenumber} sends an INITIATE to Coordinator")
            self.start_time = timer()

    def queue_handler(self, myqueue):
        while not self.terminated:
            workitem = myqueue.get()
            if workitem.event in self.eventhandlers:
                self.on_pre_event(workitem)
                self.eventhandlers[workitem.event](eventobj=workitem)  # call the handler
            else:
                print(f"Event Handler: {workitem.event} is not implemented")
            myqueue.task_done()

    def connect_me_to_channel(self, name, channel):

        try:
            self.connectors[name] = channel
        except AttributeError:
            # self.connectors = ConnectorList()
            self.connectors[name] = channel

    def on_connected_to_channel(self, name, channel):
        print(f"Connected channel-{name} by component-{self.componentinstancenumber}:{channel.componentinstancenumber}")

    def trigger_event(self, eventobj: Event):
        self.inputqueue.put_nowait(eventobj)

    def on_pre_event(self, event):
        pass
        
    def send_self(self, event: Event):
        self.trigger_event(event)
