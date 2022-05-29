import queue
from threading import Thread
from multiprocessing import Queue
from timeit import default_timer as timer
from .Experimentation.Topology import *
from .Generics import *



class GenericModel:
    

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, child_conn=None, node_queues=None, channel_queues=None):
        self.topology = topology
        self.child_conn = child_conn
        self.node_queues=node_queues
        self.channel_queues=channel_queues
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
        logger.info(f"Generated NAME:{self.componentname} COMPID: {self.componentinstancenumber}")

        try:
            if self.connectors is not None:
                pass
        except AttributeError:
            self.connectors = ConnectorList()
            logger.debug(f"NAME:{self.componentname} COMPID: {self.componentinstancenumber} created connector list")
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
            #logger.error(f"Cannot send message to DOWN Connector {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")
            pass
        try:
            src = int(self.componentinstancenumber)
            event.eventsource = None # for avoiding thread.lock problem
            if self.channel_queues is not None:
                n = len(self.channel_queues[0])
                for i in range(n):
                    dest = i
                    if self.channel_queues[src][dest] is not None:
                        self.channel_queues[src][dest].put(event)
        except Exception as e:
            logger.error(f"Cannot send message to DOWN Connector over queues {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")


    def send_up_from_channel(self, event: Event, loopback = False):
        try:
            #self.connectors[ConnectorTypes.UP].eventhandlers[EventTypes.MFRB](event)
            if loopback: # loopback is only valid in symmetric channel constructors of the topology class
                for p in self.connectors[ConnectorTypes.UP]:
                        p.trigger_event(event)
            else:
                for p in self.connectors[ConnectorTypes.UP]:
                    if p.componentinstancenumber != event.eventsource_componentinstancenumber: #TO AVOID LOOPBACK provide the loopback optional parameter
                        p.trigger_event(event)

        except Exception as e:
            #logger.error(f"Cannot send message to UP Connector from channel {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")
            pass

        try:
            src = int(event.fromchannel.split("-")[0]) 
            dest = int(event.fromchannel.split("-")[1])
            event.eventsource = None # for avoiding thread.lock problem
            if self.node_queues is not None:
                if self.node_queues[src][dest] is not None:
                    try:
                        self.node_queues[src][dest].put(event) 
                        pass
                    except Exception as ex:
                        logger.error(f"Cannot put to queue {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")
        except Exception as ex:
            logger.error(f"Cannot send message to UP Connector from channel {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")

    def send_up(self, event: Event):
        try:
            #self.connectors[ConnectorTypes.UP].eventhandlers[EventTypes.MFRB](event)
            for p in self.connectors[ConnectorTypes.UP]:
                p.trigger_event(event)

        except Exception as e:
            logger.error(f"Cannot send message to UP Connector {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")

    def send_peer(self, event: Event):
        try:
            for p in self.connectors[ConnectorTypes.PEER]:
                p.trigger_event(event)
        except Exception as e:
            logger.error(f"Cannot send message to PEER Connector {self.componentname}-{self.componentinstancenumber} {str(event)} {e}")

    def U(self, component):
        self.connect_me_to_component(ConnectorTypes.UP, component)
  
    def D(self, component):
        self.connect_me_to_component(ConnectorTypes.DOWN, component)
  
    def P(self, component):
        self.connect_me_to_component(ConnectorTypes.PEER, component)
    
    def connect_me_to_component(self, name, component):
        logger.debug(f"Connecting {self.componentname}-{self.componentinstancenumber} {name} to {component.componentname}-{component.componentinstancenumber}")
        #self.connectors[name] = component
        try:
            self.connectors[name] = component
        except AttributeError:
            self.connectors = ConnectorList()
            self.connectors[name] = component

    def on_message_from_bottom(self, eventobj: Event):
        logger.debug(f"{EventTypes.MFRB} is not handled  {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_top(self, eventobj: Event):
        logger.debug(f"{EventTypes.MFRT} is not handled  {self.componentname}.{self.componentinstancenumber}")
        pass
        #if self.child_conn is not None:
        #    self.child_conn.send("Channel Deneme")

    def on_message_from_peer(self, eventobj: Event):
        logger.debug(f"{EventTypes.MFRP} is not handled  {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_exit(self, eventobj: Event):
        logger.debug(f"{EventTypes.EXIT} is not handled  {self.componentname}.{self.componentinstancenumber} exiting")
        self.terminated = True
    

    def on_init(self, eventobj: Event):
        logger.debug(f"{EventTypes.INIT} is not handled {self.componentname}.{self.componentinstancenumber} exiting")
        

         
    def queue_handler(self, myqueue):
        while not self.terminated:
            workitem = myqueue.get()
            if workitem.event in self.eventhandlers:
                self.on_pre_event(workitem)
                logger.debug(f"{self.componentname}-{self.componentinstancenumber} will handle {workitem.event}")
                self.eventhandlers[workitem.event](eventobj=workitem)  # call the handler
            else:
                logger.error(f"{self.componentname}.{self.componentinstancenumber} Event Handler: {workitem.event} is not implemented")
            myqueue.task_done()

    def on_connected_to_component(self, name, channel):
        logger.debug(f"Connected channel-{name} by component-{self.componentinstancenumber}:{channel.componentinstancenumber}")
        
        pass

    def trigger_event(self, eventobj: Event):
        logger.debug(f"{self.componentname}.{self.componentinstancenumber} invoked with {str(eventobj)}")
        self.inputqueue.put_nowait(eventobj)

    def on_pre_event(self, event):
        logger.debug(f"{self.componentname}.{self.componentinstancenumber} invoked with {str(event)} will run on_pre_event here")
        pass
        
    def send_self(self, event: Event):
        logger.debug(f"{self.componentname}.{self.componentinstancenumber} invoking itself with {str(event)}")
        self.trigger_event(event)
