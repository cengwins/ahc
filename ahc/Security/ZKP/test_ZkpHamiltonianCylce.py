import ZkpHamiltonianCycle
from ahc.Ahc import Topology
from ahc.Channels.Channels import P2PFIFOPerfectChannel


# May delete this file after testing, change the public graph module to change node size
def main():
    topo = Topology()
    topo.construct_sender_receiver(ZkpHamiltonianCycle.ProverAdHocNode, ZkpHamiltonianCycle.VerifierAdHocNode, P2PFIFOPerfectChannel)

    topo.start()
    while True:
        continue


if __name__ == "__main__":
    main()
