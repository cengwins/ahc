from Ahc import Topology
from Channels.Channels import Channel
from PublicKeyAuth import *


def main():
    topology = Topology()
    topology.construct_sender_receiver(HostNode,AliceNode,Channel)
    topology.start()

    while True: pass

if __name__ == "__main__":
    main()





