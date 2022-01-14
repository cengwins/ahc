import os
import sys

sys.path.insert(0, os.getcwd())

from MAC.RipeMAC import RipeMac


from Ahc import ComponentRegistry, Event, ConnectorTypes, EventTypes

from SKID3 import SKID3

def runSKID3Test(keyAlice: bytes, keyBob: bytes):
    """Creates a simple topology that runs the SKID3 mutual authentication protocol.
    The peers are called Alice and Bob. When Alice is initialized, it starts authenticating
    with Bob. The resulting states of both are printed to stdout.
    
    The topology used in this test:
    ```
        RIPE-MAC(1)      RIPE-MAC(2)
            |                |
          Alice ----------- Bob
    ```"""
    registry = ComponentRegistry()
    ripeMac1 = RipeMac("RIPE-MAC", 1)
    ripeMac2 = RipeMac("RIPE-MAC", 2)
    ripeMac1.on_init(None)
    ripeMac2.on_init(None)
    
    alice = SKID3.Alice("Alice", 1, secretKey=keyAlice)
    bob = SKID3.Bob("Bob", 2, secretKey=keyBob)
    
    alice.connect_me_to_component(ConnectorTypes.UP, ripeMac1)
    ripeMac1.connect_me_to_component(ConnectorTypes.DOWN, alice)

    bob.connect_me_to_component(ConnectorTypes.UP, ripeMac2)
    ripeMac2.connect_me_to_component(ConnectorTypes.DOWN, bob)

    alice.connect_me_to_component(ConnectorTypes.PEER, bob)
    bob.connect_me_to_component(ConnectorTypes.PEER, alice)

    alice.send_self(Event(None, EventTypes.INIT, None))
    bob.send_self(Event(None, EventTypes.INIT, None))
    while not alice.terminated or not bob.terminated:
        pass
    else:
        print(f"Alice and Bob terminated. Their states: Alice={alice.state}, Bob={bob.state}")


def main():
    secretKey1 = b'\x11\xAB\xCD\xEF\x12\x34\x56\x78'
    secretKey2 = b'\x11\xAB\xCD\xEF\x1F\xA4\x16\x79'
    runSKID3Test(secretKey1, secretKey1)    # will result in success
    runSKID3Test(secretKey1, secretKey2)    # will result in fail

if __name__ == "__main__":
    main()