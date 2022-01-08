import os
import sys
from Ahc import Topology
from CryptoProtocols.ZkpHamiltonianCycle import PeggyAdHocNode, VictorAdHocNode
from Channels.Channels import P2PFIFOPerfectChannel

sys.path.insert(0, os.getcwd())


def main():
    topo = Topology()
    topo.construct_sender_receiver(PeggyAdHocNode, VictorAdHocNode, P2PFIFOPerfectChannel)

    topo.start()
    while True:
        pass


if __name__ == "__main__":
    main()
