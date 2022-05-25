import queue
from threading import Thread
from multiprocessing import Queue
from timeit import default_timer as timer

from .Experimentation.Topology import *
from .Generics import *
import pickle

class GenericModel:
    

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
        self.topology = topology
        self.child_conn = child_conn
        self.node_queues=node_queues
        self.channel_queues=channel_queues
        #print("Topology", topology)
        self.context = context
        self.components  = []
        self.configurationparameters = configurationparameters
        self.eventhandlers = {EventTypes.INIT: self.on_init, EventTypes.MFRB: self.on_message_from_bottom,
                            EventTypes.MFRT: self.on_message_from_top, EventTypes.MFRP: self.on_message_from_peer, EventTypes.EXIT: self.on_exit}
        # Add default handlers to all instantiated components.
        # If a component overwrites the __init__ method it has to call the super().__init__ method
        self.inputqueue = queue.Queue()
        self.componentname = componentname
        self.componentinstancenumber = componentinstancenumber
        self.num_worker_threads = num_worker_threads
        #self.connectors = {}
        self.terminatestarted = False
        self.terminated = False
        self.initeventgenerated = False

        self.t = [None]*self.num_worker_threads
        for i in range(self.num_worker_threads):
            self.t[i] = Thread(target=self.queue_handler, args=[self.inputqueue])
            self.t[i].daemon = True
            self.t[i].start()

        # self.mpqueuethread = Thread(target=self.mp_queue_handler, args=[self.node_queues])
        # self.mpqueuethread.daemon = True
        # self.mpqueuethread.start()

        # self.mp_conn_thread = Thread(target=self.mp_pipe_handler, args=[])
        # self.mp_conn_thread.daemon = True
        # self.mp_conn_thread.start()

        try:
            if self.connectors is not None:
                pass
        except AttributeError:
            self.connectors = ConnectorList()
            # self.connectors = ConnectorList()

        #TODO: Handle This Part
        # for i in range(self.num_worker_threads):
        #     t = Thread(target=self.queue_handler, args=[self.inputqueue])
        #     t.daemon = True
        #     t.start()

        # self.registry = ComponentRegistry()
        # self.registry.add_component(self)


    def initiate_process(self):
        self.trigger_event(Event(self, EventTypes.INIT, None))
        self.initeventgenerated = True
        for c in self.components:
            #c.inputqueue.put_nowait(Event(self, EventTypes.INIT, None))
            #c.trigger_event(Event(self, EventTypes.INIT, None))
            c.initiate_process()
        #self.inputqueue.put_nowait(Event(self, EventTypes.INIT, None))
        


    def exit_process(self):
        for c in self.components:
            #c.inputqueue.put_nowait(Event(self, EventTypes.EXIT, None))
            c.trigger_event(Event(self, EventTypes.EXIT, None))
        #self.inputqueue.put_nowait(Event(self, EventTypes.EXIT, None))
        self.trigger_event(Event(self, EventTypes.EXIT, None))
        

    
    def send_down(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.DOWN]:
                p.trigger_event(event)
        except Exception as e:
            #raise(f"Cannot send message to Down Connector {self.componentname } -- {self.componentinstancenumber}")
            #print("Exception ", e)
            pass
        try:
            src = int(self.componentinstancenumber)
            event.eventsource = None # for avoiding thread.lock problem
            if self.channel_queues is not None:
                n = len(self.channel_queues[0])
                for i in range(n):
                    dest = i
                    if self.channel_queues[src][dest] is not None:
                        print("\033[93m SENDDOWN:\033[0m", self.componentname, "-", src, " sends message to channel ", src,"-",dest)
                        self.channel_queues[src][dest].put(event)
        except Exception as e:
            #raise(f"Cannot send message to Down Connector {self.componentname } -- {self.componentinstancenumber}")
            #print("Exception ", e)
            pass

    def send_up_from_channel(self, event: Event):
        try:
            src = int(event.fromchannel.split("-")[0]) 
            dest = int(event.fromchannel.split("-")[1])
            event.eventsource = None # for avoiding thread.lock problem
            #print(self.componentinstancenumber, "Sending", event.eventcontent, event.fromchannel )
            if self.node_queues is not None:
                if self.node_queues[src][dest] is not None:
                    print("\033[92m SENDUP:\033[0m",self.componentname, self.componentinstancenumber, "to to node queues ", src, "-", dest)
                    try:
                        self.node_queues[src][dest].put(event) 
                        pass
                    except Exception as ex:
                        print("\033[93m" + "Exception when putting to queue")
                    #myev:Event = self.node_queues[src][dest].get(block=True, timeout=0.0001)
                    #print("My Event LOOPBACK ", str(myev))
        except Exception as ex:
            print("Exception at send_up_from_channel", ex)

    def send_up(self, event: Event):
        try:
            #self.connectors[ConnectorTypes.UP].eventhandlers[EventTypes.MFRB](event)
            for p in self.connectors[ConnectorTypes.UP]:
                p.trigger_event(event)

        except Exception as e:
            pass
            #raise(f"Cannot send message to UP Connector {self.componentname } -- {self.componentinstancenumber}")

    def send_peer(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.PEER]:
                p.trigger_event(event)
        except Exception as e:
            pass
            #raise(f"Cannot send message to UP Connector {self.componentname } -- {self.componentinstancenumber}")

    def connect_me_to_component(self, name, component):
        #self.connectors[name] = component
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_message_from_bottom(self, eventobj: Event):
        print(f"{EventTypes.MFRB} {self.componentname}.{self.componentinstancenumber}")

    def on_message_from_top(self, eventobj: Event):
        print(f"{EventTypes.MFRT}  {self.componentname}.{self.componentinstancenumber}")
        #if self.child_conn is not None:
        #    self.child_conn.send("Channel Deneme")

    def on_message_from_peer(self, eventobj: Event):
        print(f"{EventTypes.MFRP}  {self.componentname}.{self.componentinstancenumber}")

    def on_exit(self, eventobj: Event):
        #print(f"{EventTypes.EXIT}  {self.componentname}.{self.componentinstancenumber} exiting")
        self.terminated = True
    

    def on_init(self, eventobj: Event):
        pass

         
    def queue_handler(self, myqueue):
        while not self.terminated:
            workitem = myqueue.get()
            #print(self.componentname, self.componentinstancenumber, ": will process", workitem.event)
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
            self.connectors = ConnectorList()
            self.connectors[name] = channel
        connectornameforchannel = self.componentname + str(self.componentinstancenumber)
        channel.connect_me_to_component(connectornameforchannel, self)
        self.on_connected_to_channel(name, channel)

    def on_connected_to_channel(self, name, channel):
        #print(f"Connected channel-{name} by component-{self.componentinstancenumber}:{channel.componentinstancenumber}")
        pass

    def trigger_event(self, eventobj: Event):
        self.inputqueue.put_nowait(eventobj)

    def on_pre_event(self, event):
        pass
        
    def send_self(self, event: Event):
        self.trigger_event(event)
