-import os
import sys

sys.path.insert(0, os.getcwd())

from random import choice
from Schnorr import Prover, Verifier
from Channels.Channels import Channel
from Ahc import Topology

def simulate_verified_knowledge():

    topo = Topology()

    topo.construct_sender_receiver(Prover, Verifier, Channel)

    topo.start()


def main():

    # Generate System Variables
    
    # Generate P
    #print("Generating 1024-bit prime number.")
    #P = generate_prime_number()

    #print("1024-bit Prime Number : ", P)

    # Generate Q
    #print("Generating divisor of P-1.")
    #Q = select_random_divisor(P-1)

    #print("Divisor of P-1 : ", Q)

    # Generate G

    # Simulate Verified Knowledge



    simulate_verified_knowledge()

    while True: pass

if __name__ == "__main__":
    main()