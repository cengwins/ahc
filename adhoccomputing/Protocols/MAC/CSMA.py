from ahc.Ahc import Event, EventTypes, ComponentConfigurationParameters
from ahc.MAC.GenericMAC import GenericMac, GenericMacEventTypes
import time, random, math

class MacCsmaPPersistentConfigurationParameters (ComponentConfigurationParameters):
    def __init__(self, p):
        self.p = p

class MacCsmaPPersistent(GenericMac):
    
    #Constructor
    def __init__(self, componentname, componentinstancenumber, configurationparameters:MacCsmaPPersistentConfigurationParameters):
        super().__init__(componentname, componentinstancenumber)
        self.p = configurationparameters.p
    
    #on_init will be called from topo.start to initialize components
    def on_init(self, eventobj: Event):
        self.retrialcnt = 0
        super().on_init(eventobj)  # required because of inheritence
        #print("Initialized", self.componentname, ":", self.componentinstancenumber)

    def handle_frame(self):
        #TODO: not a good solution put message in queue, schedule a future event to retry yhe first item in queueu    
        #print("handle_frame")
        if self.framequeue.qsize() > 0:
            #print("handle_frame", "queue not empty")
            randval = random.random()
            if randval < self.p: # TODO: Check if correct
                clearmi, powerdb  = self.ahcuhd.ischannelclear(threshold=-35)
                #print("Component:", self.componentinstancenumber, "clear mi=", clearmi, " Power=", powerdb)
                if  clearmi == True:
                    try:
                        eventobj = self.framequeue.get()
                        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
                        self.send_down(evt)
                        self.retrialcnt = 0
                    except Exception as e:
                        print("MacCsmaPPersistent handle_frame exception, ", e)
                else:
                    self.retrialcnt = self.retrialcnt + 1
                    time.sleep(random.randrange(0,math.pow(2,self.retrialcnt))*0.001)
                    #print("Busy")
        else:
            #print("Queue size", self.framequeue.qsize())
            pass
        time.sleep(0.00001) # TODO: Think about this otherwise we will only do cca
        self.send_self(Event(self, GenericMacEventTypes.HANDLEMACFRAME, None)) #Continuously trigger handle_frame
        
            
                
                