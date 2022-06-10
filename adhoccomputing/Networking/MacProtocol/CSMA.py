from ...Generics import *
from .GenericMAC import GenericMac, GenericMacEventTypes
import time, random, math


class ComponentConfigurationParameters():
    pass

class MacCsmaPPersistentConfigurationParameters (ComponentConfigurationParameters):
    def __init__(self, p, cca_threshold = -35):
        self.p = p
        self.cca_threshold = cca_threshold

class MacCsmaPPersistent(GenericMac):
    
    #Constructor
    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None, sdr=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology, sdr)
        self.p = configurationparameters.p
        self.cca_threshold = configurationparameters.cca_threshold
    
    #on_init will be called from topo.start to initialize components
    def on_init(self, eventobj: Event):
        self.retrialcnt = 0
        super().on_init(eventobj)  # required because of inheritence
        #logger.debug(f"{self.componentname}.{self.componentinstancenumber} RECEIVED {str(eventobj)}")

    def handle_frame(self):
        #TODO: not a good solution put message in queue, schedule a future event to retry yhe first item in queueu    
        if self.framequeue.qsize() > 0:
            randval = random.random()
            if randval < self.p: # TODO: Check if correct
                clearmi, powerdb  = self.sdrdev.ischannelclear(threshold=self.cca_threshold)
                if  clearmi == True:
                    try:
                        eventobj = self.framequeue.get()
                        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
                        self.send_down(evt)
                        self.retrialcnt = 0
                    except Exception as e:
                        logger.critical(f"MacCsmaPPersistent handle_frame exception {e}")
                else:
                    self.retrialcnt = self.retrialcnt + 1
                    time.sleep(random.randrange(0,math.pow(2,self.retrialcnt))*0.001)
        else:
            pass
        time.sleep(0.00001) # TODO: Think about this otherwise we will only do cca
        self.send_self(Event(self, GenericMacEventTypes.HANDLEMACFRAME, None)) #Continuously trigger handle_frame
        
            
                
                