import os
import sys
from enum import Enum
from Ahc import Topology
from CryptoProtocols.ZkpHamiltonianCycle import ProverAdHocNode, VerifierAdHocNode, ProverType
from Channels.Channels import P2PFIFOPerfectChannel

sys.path.insert(0, os.getcwd())


class ChallengeBias(Enum):
    NORMAL = 0.5
    MOSTLY_PROVE_GRAPH = 0.75
    ONLY_PROVE_GRAPH = 1.5
    MOSTLY_SHOW_CYCLE = 0.25
    ONLY_SHOW_CYCLE = -1.5


def test_honest_prover():
    print(f"\nTest Completeness (with honest prover)")
    topo = Topology()
    ProverAdHocNode.set_properties(ProverType.HONEST)
    VerifierAdHocNode.set_properties(max_trials[0], challenge_bias[0].value)
    topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
    topo.start()


def test_dishonest_prover_fake_graph():
    print(f"\nTest Soundness (with dishonest prover: fake graph)")
    topo = Topology()
    ProverAdHocNode.set_properties(ProverType.DISHONEST_FAKE_GRAPH)
    topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
    topo.start()


def test_dishonest_prover_fake_cycle():
    print(f"\nTest Soundness (with dishonest prover: fake cycle)")
    topo = Topology()
    ProverAdHocNode.set_properties(ProverType.DISHONEST_FAKE_CYCLE)
    topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
    topo.start()


def main():
    test_honest_prover()
    #test_dishonest_prover_fake_graph()
    #test_dishonest_prover_fake_cycle()
    while True:
        pass


if __name__ == "__main__":
    max_trials = [1, 2, 5, 10]
    challenge_bias = [ChallengeBias.NORMAL,
                      ChallengeBias.MOSTLY_PROVE_GRAPH,
                      ChallengeBias.ONLY_PROVE_GRAPH,
                      ChallengeBias.MOSTLY_SHOW_CYCLE,
                      ChallengeBias.ONLY_SHOW_CYCLE]
    main()
