import base64

import warnings
from math import e
import random
import string

from cryptography.hazmat.primitives import hashes
from ahc.Ahc import *
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.exceptions import InvalidSignature  



component_reg = ComponentRegistry()






"""


(1)[DONE] Alice performs a computation based on some random numbers and
her private key and sends the result to the host.(hers publice-key)



(2)[DONE] The host sends Alice a different random number.(his public-key)


(3)[] Alice makes some computation based on the random numbers (both
the ones she generated and the one she received from the host) and her
private key, and sends the result to the host.



(4) The host does some computation on the various numbers received
from Alice and her public key to verify that she knows her private key.




(5) If she does, her identity is verified.



"""
    


warnings.filterwarnings("ignore")




class Alice(ComponentModel):



    def on_init(self, eventobj: Event):
        print("Alice has been created !!!")

        self.private_key = rsa.generate_private_key(public_exponent=65537,
                                                    key_size=2048,
                                                    )
        self.public_key = self.private_key.public_key()

        self.false_private_key = rsa.generate_private_key(public_exponent=65537,
                                                    key_size=2048,
                                                    )
        self.false_public_key = self.false_private_key.public_key()

        payload = [self.componentname,"KEY",self.public_key]

        # Send public key to channel        
        key_event = Event(self,EventTypes.MFRT,payload)
        self.send_down(key_event)




    def on_message_from_bottom(self, eventobj: Event):

        payload_in = eventobj.eventcontent

        #Host sent its public key so Alice need to
        #Try to login
        if payload_in[1] == "KEY":
            print("Alice got Host's public-key")
            self.host_public_key = payload_in[2]

            # After getting message from below 
            # Alice needs to sign a message then Host can 
            # try to validate it. 
            # Let's create a random string in 32 character long
            S = 32  # number of characters in the string.  
            message = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            
            message_bytes = bytes(message,encoding='utf-8')

            ciphertext = self.host_public_key.encrypt(
                            message_bytes,
                            padding.OAEP(
                                    mgf=padding.MGF1(algorithm=hashes.SHA1()),
                                    algorithm=hashes.SHA1(),
                                    label=None
                                )
                        )   

            ciphertext  = str(base64.b64encode(ciphertext), encoding='utf-8')

            signer = self.private_key.signer(
                                    padding.PSS(
                                                mgf=padding.MGF1(hashes.SHA256()),
                                                salt_length=padding.PSS.MAX_LENGTH
                                            ),hashes.SHA256()
                                    )
            signer.update(message_bytes)
            signature = str(base64.b64encode(signer.finalize()),encoding='utf8')

            data = (ciphertext,signature)

            payload_out = [self.componentname,"LOGIN",data]
            login_event = Event(self,EventTypes.MFRT,payload_out)
            self.send_down(login_event)

        elif payload_in[1] == "OK":
            #Host has successfully authed Alice
            print("Alice has been authorized")
        elif payload_in[1] == "FAIL":
            #Host denied Alice
            print("Alice has been denied") 

class AliceNode(ComponentModel):

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self,componentname,componentid):

        self.Alice = Alice("Alice",componentid)
        self.Alice.connect_me_to_component(ConnectorTypes.DOWN,self)
        self.connect_me_to_component(ConnectorTypes.UP,self.Alice)
        super().__init__(componentname,componentid)

class HostNode(ComponentModel):

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self,componentname,componentid):

        self.Host = Host("Host",componentid)
        self.Host.connect_me_to_component(ConnectorTypes.DOWN,self)
        self.connect_me_to_component(ConnectorTypes.UP,self.Host)
        super().__init__(componentname,componentid)



class Host(ComponentModel):

    def on_init(self,eventobj:Event):
        print("Host has been created!!!")
        #Generate public private key pairs
        self.private_key = rsa.generate_private_key(public_exponent=65537,
                                                    key_size=2048,
                                                    )
        self.public_key = self.private_key.public_key()
        self.alice_public_key = None



    def on_message_from_bottom(self, eventobj: Event):

        #When message came from bottom need to decide wheter
        #this message is Alice's public-key or login trial
        
        payload_in=eventobj.eventcontent

        # Alice sent hers pub-key
        if payload_in[1] == "KEY":
            #Save alice's public key
            print("Host got somebody's public-key")
            self.alice_public_key = payload_in[2]
            payload_out = [self.componentname,"KEY",self.public_key]
            key_event = Event(self,EventTypes.MFRT,payload_out)
            self.send_down(key_event)
        
        elif payload_in[1] == "LOGIN":
            print("Somebody tries to login")
            ciphertext = payload_in[2][0]
            signature  = payload_in[2][1]
            ciphertext_decoded = base64.b64decode(ciphertext) 
            #if not isinstance(ciphertext, bytes) else ciphertext
            plain_text = self.private_key.decrypt(ciphertext_decoded,
                         padding.OAEP(padding.MGF1(algorithm=hashes.SHA1()),
                         hashes.SHA1(), None))
            plain_text = str(plain_text, encoding='utf8')


            try:
                plain_text_bytes = bytes(plain_text,encoding='utf8') 
                #if not isinstance(plain_text, bytes) else plain_text
                signature = base64.b64decode(signature) 
                #if not isinstance(signature, bytes) else signature
                verifier = self.alice_public_key.verifier(
                                                        signature,
                                                        padding.PSS(
                                                            mgf=padding.MGF1(hashes.SHA256()),
                                                            salt_length=padding.PSS.MAX_LENGTH
                                                        ),
                                                        hashes.SHA256()
                )
                verifier.update(plain_text_bytes)
                verifier.verify()

                payload_out = [self.componentname,"OK"]
                key_event = Event(self,EventTypes.MFRT,payload_out)
                self.send_down(key_event)
                
            except InvalidSignature:
                payload_out = [self.componentname,"FAIL"]
                key_event = Event(self,EventTypes.MFRT,payload_out)
                self.send_down(key_event)


        







