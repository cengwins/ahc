import os
import sys
import time
sys.path.insert(0, os.getcwd())
import time
import cv2


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import *
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.NetworkLayer.GenericNetworkLayer import GenericNetworkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.Networking.ApplicationLayer.OpenCVVideoStreamingApp import *
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import  UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters
from adhoccomputing.Networking.ApplicationLayer.MessageSegmentation import *
import logging


macconfig = MacCsmaPPersistentConfigurationParameters(0.5, -50)
sdrconfig = SDRConfiguration(freq =915000000.0, bandwidth = 5000000, chan = 0, hw_tx_gain = 70, hw_rx_gain = 30, sw_tx_gain = -12.0)

appconfig = OpenCVVideoStreamingAppConfig(5)


class AdHocNode(GenericModel):

    def on_init(self, eventobj: Event):
        logger.applog(f"Initializing {self.componentname}.{self.componentinstancenumber}")
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj)

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        # SUBCOMPONENTS
        
        self.appl = OpenCVVideoStreamingApp("OpenCVVideoStreamingApp", componentinstancenumber, topology=topology, configurationparameters=appconfig)
        self.seg = MessageSegmentation("MessageSegmentation", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, topology=topology,usrpconfig=sdrconfig, )
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber,  configurationparameters=macconfig, sdr=self.phy.sdrdev, topology=topology)

        self.components.append(self.appl)
        self.components.append(self.mac)
        self.components.append(self.seg)
        #self.components.append(self.phy)
        
        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appl.connect_me_to_component(ConnectorTypes.UP, self) #Not required if nodemodel will do nothing
        self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.seg)

        self.seg.connect_me_to_component(ConnectorTypes.UP, self.appl)
        self.seg.connect_me_to_component(ConnectorTypes.DOWN, self.mac)
        
        self.mac.connect_me_to_component(ConnectorTypes.UP, self.seg)
        self.mac.connect_me_to_component(ConnectorTypes.DOWN, self.phy)
        
        # Connect the bottom component to the composite component....
        self.phy.connect_me_to_component(ConnectorTypes.UP, self.mac)
        self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        
        # self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        # self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)


def main():

    #NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
    setAHCLogLevel(25)
    setAHCLogLevel(logging.INFO)
    topo = Topology()
    #topo.construct_sender_receiver(AdHocNode, AdHocNode, GenericChannel)
    topo.construct_winslab_topology_without_channels_for_docker(AdHocNode, 0)

    
    

    cap = cv2.VideoCapture(0)
    cap.set(3,640)
    cap.set(4,480)
    #cv2.startWindowThread()
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    #out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (640,480))
    cv2.namedWindow('frame')
    logger.applog(f"Frame rate will be {appconfig.framerate}")
    topo.start()
    time.sleep(3)
    topo.nodes[0].phy.trigger_event(Event(None, EventTypes.INIT, ""))
    #topo.nodes[0].appl.send_self(Event(None, OpenCVVideoStreamingAppEventTypes.STARTSTREAMING, ""))
    while(True):
        frame = topo.nodes[0].appl.frame
        if frame is not None:
            #out.write(frame)
            frameresized = cv2.resize(frame, (640,480))
            cv2.imshow('frame', frame)
            c = cv2.waitKey(1)
            if c & 0xFF == ord('q'):
                break

    cap.release()
    #out.release()
    cv2.destroyAllWindows()

    topo.exit()
    time.sleep(5)

if __name__ == "__main__":
    main()
