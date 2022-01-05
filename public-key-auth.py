from Ahc import Ahc, ComponentModel, ComponentRegistry



component_reg = ComponentRegistry()






"""


(1) Alice performs a computation based on some random numbers and
her private key and sends the result to the host.


(2) The host sends Alice a different random number.


(3) Alice makes some computation based on the random numbers (both
the ones she generated and the one she received from the host) and her
private key, and sends the result to the host.



(4) The host does some computation on the various numbers received
from Alice and her public key to verify that she knows her private key.




(5) If she does, her identity is verified.



"""







class Alice(ComponentModel):
    pass


class Host(ComponentModel):
    pass





