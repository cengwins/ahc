from Ahc import Topology
from Channels.Channels import P2PFIFOPerfectChannel
from PublicKeyAuth import *


def main():
    topology = Topology()
    topology.construct_sender_receiver(HostNode,AliceNode,P2PFIFOPerfectChannel)
    topology.start()
    topology.plot()

    while True: pass

if __name__ == "__main__":
    main()





