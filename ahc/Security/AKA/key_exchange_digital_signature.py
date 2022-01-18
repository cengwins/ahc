from cryptography.hazmat.primitives import hashes
from ahc.Ahc import *
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.exceptions import InvalidSignature  
from cryptography.hazmat.primitives import serialization








#TO DO: Trent creates a public key/private key pair, and announces its public key.

#Bob and Alice creates public key/private key pair and sends their public key to Trent.

#Trent signs the public keys of Bob and Alice (by encrypting them with its private key) and sends these to Alice and Bob respectively.

#Alice and Bob decrypt the keys with Trents public key, therefore ensuring that they are the write keys. 

#Then they use those keys during message exchange.






class Alice(ComponentModel):



    def on_init(self, eventobj: Event):

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        
    def on_message_from_bottom(self, eventobj: Event):
        #self.on_message_from_bottom_naive(eventobj)
        self.on_message_from_bottom_protocol(eventobj)
        

    def on_message_from_bottom_naive(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagetype == 2):
            self.t_public_key = eventobj.eventcontent.payload
            print(f"I am Alice and I just received Trent's public key")
            self.send_public_key()
        elif(eventobj.eventcontent.header.messagetype == 0):

                self.bob_public_key = eventobj.eventcontent.payload
                print(f"I am Alice and I just received Bob's public key from Trent")
                self.send_messages()

        else:
            ciphertext = eventobj.eventcontent.payload
            plaintext = self.private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                    )
                    )

            print(f"I am {self.componentname}, and I received a message from Bob: {plaintext}\n")


    def on_message_from_bottom_protocol(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagetype == 2):
            self.t_public_key = eventobj.eventcontent.payload
            print(f"I am Alice and I just received Trent's public key")
            self.send_public_key()
        elif(eventobj.eventcontent.header.messagetype == 0):



            signature = eventobj.eventcontent.payload[0]
            message = eventobj.eventcontent.payload[1]

            try:
                self.t_public_key.verify(signature,
                                        message,
                                        padding.PSS(
                                        mgf=padding.MGF1(hashes.SHA256()),
                                        salt_length=padding.PSS.MAX_LENGTH
                                        ),
                                        hashes.SHA256()
                                        )
                self.bob_public_key = eventobj.eventcontent.payload[2]
                print(f"I am Alice and I just received Bob's public key from Trent")
                self.send_messages()
            except InvalidSignature:
                print("Hey! This public key is not from Trent")

        else:
            ciphertext = eventobj.eventcontent.payload
            plaintext = self.private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                    )
                    )

            print(f"I am {self.componentname}, and I received a message from Bob: {plaintext}\n")

    def send_messages(self):
        message = b"Hi this is first message from Alice to Bob"
        ciphertext = self.bob_public_key.encrypt(
                        message,
                        padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
                    )
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 1,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "1-2")
        message = GenericMessage(header, ciphertext)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)

    def send_public_key(self):
        print("I am Alice and I am sending my public key")
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = TrentNode,
            nexthop = TrentNode,
            interfaceid = "0-1")
        message = GenericMessage(header, self.public_key)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)




class Bob(ComponentModel):

    def on_init(self,eventobj:Event):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

    def on_message_from_bottom(self, eventobj: Event):
        #self.on_message_from_bottom_naive(eventobj)
        self.on_message_from_bottom_protocol(eventobj)
        

    def on_message_from_bottom_naive(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagetype == 2):
            self.t_public_key = eventobj.eventcontent.payload
            print(f"I am Bob and I just received Trent's public key")
            self.send_public_key()
        elif(eventobj.eventcontent.header.messagetype == 0):

                self.bob_public_key = eventobj.eventcontent.payload
                print(f"I am Bob and I just received Alice's public key from Trent")
                self.send_messages()

        else:
            ciphertext = eventobj.eventcontent.payload
            plaintext = self.private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                    )
                    )

            print(f"I am {self.componentname}, and I received a message from Alice: {plaintext}\n")


    def on_message_from_bottom_protocol(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagetype == 2):
            self.t_public_key = eventobj.eventcontent.payload
            print(f"I am Bob and I just received Trent's public key")
            self.send_public_key()
        elif(eventobj.eventcontent.header.messagetype == 0):


            signature = eventobj.eventcontent.payload[0]
            message = eventobj.eventcontent.payload[1]

            try:
                self.t_public_key.verify(signature,
                                        message,
                                        padding.PSS(
                                        mgf=padding.MGF1(hashes.SHA256()),
                                        salt_length=padding.PSS.MAX_LENGTH
                                        ),
                                        hashes.SHA256()
                                        )
                self.bob_public_key = eventobj.eventcontent.payload[2]
                print(f"I am Bob and I just received Alice's public key from Trent")
                self.send_messages()
            except InvalidSignature:
                print("Hey! This public key is not from Trent")

        else:
            ciphertext = eventobj.eventcontent.payload
            plaintext = self.private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                    )
                    )

            print(f"I am {self.componentname}, and I received a message from Alice: {plaintext}\n")

    def send_messages(self):
        message = b"Hi this is first message from Bob to Alice"
        ciphertext = self.bob_public_key.encrypt(
                        message,
                        padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
                    )
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 1,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "1-2")
        message = GenericMessage(header, ciphertext)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)

    def send_public_key(self):
        print("I am Bob and I am sending my public key")
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = TrentNode,
            nexthop = TrentNode,
            interfaceid = "0-2")
        message = GenericMessage(header, self.public_key)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)


class Trent(ComponentModel):

    def on_init(self,eventobj:Event):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        trents_public_key = self.private_key.public_key()
        self.malicious_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.malicious_public_key = self.malicious_private_key.public_key()
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 2,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "0-2")
        message = GenericMessage(header, trents_public_key)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)
        header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 2,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "0-1")
        message = GenericMessage(header, trents_public_key)
        evt = Event(self, EventTypes.MFRT, message)
        self.send_down(evt)

    def on_message_from_bottom(self, eventobj: Event):
        #self.on_message_from_bottom_naive(eventobj)
        self.on_message_from_protocol(eventobj)
        #self.on_message_from_bottom_man_in_the_middle(eventobj)
        #self.on_message_from_bottom_naive_mitm(eventobj)

    def on_message_from_bottom_naive_mitm(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagefrom == "Alice"):
            print("I am man in the middle and I am sending Bob my public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "0-2")
            message = GenericMessage(header, self.malicious_public_key)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)
        else:
            print("I am man in the middle and I am sending Alice my public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "0-1")
            message = GenericMessage(header, self.malicious_public_key)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)

    def on_message_from_bottom_naive(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagefrom == "Alice"):
            print("I am Trent and I am sending Bob Alice's public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "0-2")
            alice_public_key = eventobj.eventcontent.payload
            message = GenericMessage(header, alice_public_key)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)
        else:
            print("I am Trent and I am sending Alice Bob's public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "0-1")
            bob_public_key = eventobj.eventcontent.payload
            message = GenericMessage(header, bob_public_key)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)


    def on_message_from_bottom_man_in_the_middle(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagefrom == "Alice"):
            print("I am man in the middle and I am sending Bob my public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "0-2")
            pem = self.malicious_public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                            )
            signature = self.malicious_private_key.sign(
                        pem,
                        padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                        )
            payload = [signature, pem, self.malicious_public_key]
            message = GenericMessage(header, payload)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)
        else:
            print("I am man in the middle and I am sending Alice my public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "0-1")
            pem = self.malicious_public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                            )
            signature = self.malicious_private_key.sign(
                        pem,
                        padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                        )
            payload = [signature, pem, self.malicious_public_key]
            message = GenericMessage(header, payload)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)

    def on_message_from_protocol(self, eventobj: Event):
        if(eventobj.eventcontent.header.messagefrom == "Alice"):
            print("I am Trent and I am sending Bob Alice's public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = BobNode,
            nexthop = BobNode,
            interfaceid = "0-2")
            alice_public_key = eventobj.eventcontent.payload
            pem = alice_public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                            )
            signature = self.private_key.sign(
                        pem,
                        padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                        )
            payload = [signature, pem, alice_public_key]
            message = GenericMessage(header, payload)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)
        else:
            print("I am Trent and I am sending Alice Bob's public key")
            header = GenericMessageHeader(messagefrom = self.componentname, 
            messagetype = 0,
            messageto = AliceNode,
            nexthop = AliceNode,
            interfaceid = "0-1")
            bob_public_key = eventobj.eventcontent.payload
            pem = bob_public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                            )
            signature = self.private_key.sign(
                        pem,
                        padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                        )
            payload=[signature, pem, bob_public_key]
            message = GenericMessage(header, payload)
            evt = Event(self, EventTypes.MFRT, message)
            self.send_down(evt)



        



        





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

    def get_component_id(self):
        return self.componentid

class BobNode(ComponentModel):

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self,componentname,componentid):

        self.Bob = Bob("Bob",componentid)
        self.Bob.connect_me_to_component(ConnectorTypes.DOWN,self)
        self.connect_me_to_component(ConnectorTypes.UP,self.Bob)
        super().__init__(componentname,componentid)


class TrentNode(ComponentModel):

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self,componentname,componentid):

        self.Trent = Trent("Trent",componentid)
        self.Trent.connect_me_to_component(ConnectorTypes.DOWN,self)
        self.connect_me_to_component(ConnectorTypes.UP,self.Trent)
        super().__init__(componentname,componentid)





