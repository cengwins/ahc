import os
import sys
from enum import Enum
from Ahc import Topology
from CryptoProtocols.ZkpHamiltonianCycle import ProverAdHocNode, VerifierAdHocNode, ProverType
from Channels.Channels import P2PFIFOPerfectChannel

sys.path.insert(0, os.getcwd())


# defined biases probabilities
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
    # change below indexes
    VerifierAdHocNode.set_properties(max_trials[3], challenge_bias[0].value)
    topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
    topo.start()


def test_dishonest_prover_fake_graph():
    print(f"\nTest Soundness (with dishonest prover: fake graph)")
    # for easier view, don't use loop
    for i in range(10):
        topo = Topology()
        # change below indexes
        VerifierAdHocNode.set_properties(max_trials[3], challenge_bias[3].value)
        ProverAdHocNode.set_properties(ProverType.DISHONEST_FAKE_GRAPH)
        topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
        topo.start()


def test_dishonest_prover_fake_cycle():
    print(f"\nTest Soundness (with dishonest prover: fake cycle)")
    # for easier view, don't use loop
    for i in range(10):
        topo = Topology()
        # change below indexes
        VerifierAdHocNode.set_properties(max_trials[3], challenge_bias[4].value)
        ProverAdHocNode.set_properties(ProverType.DISHONEST_FAKE_CYCLE)
        topo.construct_sender_receiver(ProverAdHocNode, VerifierAdHocNode, P2PFIFOPerfectChannel)
        topo.start()


def main():
    test_honest_prover() # uncomment to test
    # test_dishonest_prover_fake_graph() # uncomment to test
    # test_dishonest_prover_fake_cycle() # uncomment to test
    while True:
        pass


if __name__ == "__main__":
    # used test data
    max_trials = [1, 2, 5, 10]
    challenge_bias = [ChallengeBias.NORMAL,
                      ChallengeBias.MOSTLY_PROVE_GRAPH,
                      ChallengeBias.ONLY_PROVE_GRAPH,
                      ChallengeBias.MOSTLY_SHOW_CYCLE,
                      ChallengeBias.ONLY_SHOW_CYCLE]
    main()
