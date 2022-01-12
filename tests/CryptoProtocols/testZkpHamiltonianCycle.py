import os
import sys
from Ahc import Topology
from CryptoProtocols.ZkpHamiltonianCycle import ProverAdHocNode, VerifierAdHocNode, ProverType
from Channels.Channels import P2PFIFOPerfectChannel

sys.path.insert(0, os.getcwd())


def main():
    topo = Topology()
    ProverAdHocNode.set_properties(ProverType.DISHONEST_FAKE_CYCLE)
    topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
    topo.start()
    while True:
        pass


if __name__ == "__main__":
    main()
