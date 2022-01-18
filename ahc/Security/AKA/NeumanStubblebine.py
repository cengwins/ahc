from ahc.Ahc import ComponentModel, ComponentRegistry, ConnectorTypes,Event, EventTypes, Topology
from ahc.Channels.Channels import Channel
from cryptography.fernet import Fernet
import networkx
import os
import json
import time


TIME_LIMIT_FOR_REAUTHENTICATION=86400 #number of seconds in a day

registry=ComponentRegistry()

class Alice(ComponentModel):

    def __init__(self, componentname, componentinstancenumber, trentKey):
        self.fernets={"Trent":Fernet(trentKey)}
        self.random_number=int.from_bytes(os.urandom(32),"big") #32 byte random number
        super().__init__(componentname,componentinstancenumber)

    def on_init(self, eventobj: Event):
        #step 1
        message={
            "alice_name":self.componentname,
            "alice_random_number":self.random_number
            }
        event=Event(self,EventTypes.MFRT,message)
        self.send_down(event)
        self.state=0

    def on_message_from_bottom(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        eventContent=eventobj.eventcontent

        if self.state==0:
            #step 4
            message_to_alice=eventContent["message_to_alice"]
            message_to_bob=eventContent["message_to_bob"]
            bob_random_number=eventContent["bob_random_number"]

            decrypted_part=json.loads(self.fernets["Trent"].decrypt(message_to_alice))

            bob_name=decrypted_part["bob_name"]
            alice_random_number=decrypted_part["alice_random_number"]
            session_key=decrypted_part["session_key"]
            timestamp=decrypted_part["timestamp"]

            if alice_random_number!=self.random_number:
                print(f"I am {self.componentname}, received random number does not match the initial random number\n"+
                    f"Initial random number:{self.random_number}\n"+
                    f"Received random number:{alice_random_number}\n"
                )
                return
            
            self.fernets["Bob"]=Fernet(session_key)

            message_from_alice=self.fernets["Bob"].encrypt(json.dumps({"bob_random_number":bob_random_number}).encode("utf-8"))
            message={
                "message_from_trent":message_to_bob,
                "message_from_alice":message_from_alice
            }
            event=Event(self,EventTypes.MFRT,message)
            self.send_down(event)

            time.sleep(1)

            #reauthentication step 1
            self.random_number=int.from_bytes(os.urandom(32),"big") #32 byte random number  
            message={
                "message_from_trent":message_to_bob,
                "random_number":self.random_number
            }
            self.state=1
            event=Event(self,EventTypes.MFRT,message)
            self.send_down(event)

        elif self.state==1:
            #reauthentication step 3
            bob_random_number=eventContent["random_number"]
            decrypted_part=json.loads(self.fernets["Bob"].decrypt(eventContent["encrypted_part"]))
            alice_random_number=decrypted_part["alice_random_number"]

            #check if the random number has not been changed
            if self.random_number!=alice_random_number:
                print(f"I am {self.componentname}, received random number does not match the initial random number\n"+
                f"Initial random number:{self.random_number}\n"+
                f"Received random number:{alice_random_number}\n"
                )
                return

            encrypted_part=self.fernets["Bob"].encrypt(json.dumps({"bob_random_number":bob_random_number}).encode("utf-8"))
            message={"encrypted_part":encrypted_part}
            event=Event(self,EventTypes.MFRT,message)
            self.send_down(event)



class Bob(ComponentModel):

    def __init__(self, componentname, componentinstancenumber, trentKey):
        self.fernets={"Trent":Fernet(trentKey)}
        self.random_number=int.from_bytes(os.urandom(32),"big") #32 byte random number
        self.state=0
        super().__init__(componentname,componentinstancenumber)

    def on_message_from_bottom(self, eventobj: Event):
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        eventContent=eventobj.eventcontent

        if self.state==0:
            #step 2
            self.timestamp=time.time()
            eventContent["timestamp"]=self.timestamp
            encrypted_part=self.fernets["Trent"].encrypt(json.dumps(eventContent).encode("utf-8"))
            message={
                "bob_name":self.componentname,
                "bob_random_number":self.random_number,
                "encrypted_part":encrypted_part
            }
            self.state=1
            event=Event(self,EventTypes.MFRT,message)
            self.send_down(event)
            
        elif self.state==1:
            #step 5
            message_from_trent=json.loads(self.fernets["Trent"].decrypt(eventContent["message_from_trent"]))
            alice_name=message_from_trent["alice_name"]
            session_key=message_from_trent["session_key"]
            timestamp=message_from_trent["timestamp"]

            #check if the timestamp has not been changed
            if self.timestamp!=timestamp:
                print(f"I am {self.componentname}, received timestamp does not match the initial timestamp\n"+
                f"Initial timestamp:{self.timestamp}\n"+
                f"Received timestamp:{timestamp}\n"
                )
                return

            self.fernets["Alice"]=Fernet(session_key)
            
            message_from_alice=json.loads(self.fernets["Alice"].decrypt(eventContent["message_from_alice"]))
            bob_random_number=message_from_alice["bob_random_number"]

            #check if the random number has not been changed
            if self.random_number!=bob_random_number:
                print(f"I am {self.componentname}, received random number does not match the initial random number\n"+
                f"Initial random number:{self.random_number}\n"+
                f"Received random number:{bob_random_number}\n"
                )
                return

            self.state=2
            print("Both Alice and Bob are sure of each others authenticity and they now share a secret key\n")
            print("Now Alice will wait 1 second and try to authenticate with Bob again to demonstrate the proccess in the subsequent authentications\n")
        
        elif self.state==2:
            #reauthentication step 2
            alice_random_number=eventContent["random_number"]
            message_from_trent=json.loads(self.fernets["Trent"].decrypt(eventContent["message_from_trent"]))
            alice_name=message_from_trent["alice_name"]
            session_key=message_from_trent["session_key"]
            timestamp=message_from_trent["timestamp"]

            #check if the timestamp has not been changed
            if self.timestamp!=timestamp:
                print(f"I am {self.componentname}, received timestamp does not match the initial timestamp\n"+
                f"Initial timestamp:{self.timestamp}\n"+
                f"Received timestamp:{timestamp}\n"
                )
                return

            #check if the time limit for reauthentication has passed
            current_time=time.time()
            if (timestamp+TIME_LIMIT_FOR_REAUTHENTICATION)<current_time:
                print(f"I am {self.componentname}, timestamp has expired, reauthentication not possible\n")
                return

            self.random_number=int.from_bytes(os.urandom(32),"big") #32 byte random number
            encrypted_part=Fernet(session_key).encrypt(json.dumps({"alice_random_number":alice_random_number}).encode("utf-8"))
            message={
                "random_number":self.random_number,
                "encrypted_part":encrypted_part
            }
            self.state=3
            event=Event(self,EventTypes.MFRT,message)
            self.send_up(event)

        elif self.state==3:
            #last part of reauthentication
            decrypted_part=json.loads(self.fernets["Alice"].decrypt(eventContent["encrypted_part"]))
            bob_random_number=decrypted_part["bob_random_number"]

            #check if the random number has not been changed
            if self.random_number!=bob_random_number:
                print(f"I am {self.componentname}, received random number does not match the initial random number\n"+
                f"Initial random number:{self.random_number}\n"+
                f"Received random number:{bob_random_number}\n"
                )
                return

            print("Both Alice and Bob reauthenticated with each other without relying on Trent\n")

class Trent(ComponentModel):

    def __init__(self, componentname, componentinstancenumber, aliceKey, bobKey):
        self.fernets={"Alice":Fernet(aliceKey),"Bob":Fernet(bobKey)}
        super().__init__(componentname,componentinstancenumber)

    def on_message_from_bottom(self, eventobj: Event):
        #step 3
        print(f"I am {self.componentname}, eventcontent={eventobj.eventcontent}\n")
        eventContent=eventobj.eventcontent
        decrypted_part=json.loads(self.fernets["Bob"].decrypt(eventContent["encrypted_part"]))
        bob_name=eventContent["bob_name"]
        bob_random_number=eventContent["bob_random_number"]
        alice_name=decrypted_part["alice_name"]
        alice_random_number=decrypted_part["alice_random_number"]
        timestamp=decrypted_part["timestamp"]
        session_key=Fernet.generate_key()
        message_to_alice={
            "bob_name":bob_name,
            "alice_random_number":alice_random_number,
            "session_key":session_key.decode("utf-8"),
            "timestamp":timestamp
        }
        alice_encrypted_part=self.fernets["Alice"].encrypt(json.dumps(message_to_alice).encode("utf-8"))
        message_to_bob={
            "alice_name":alice_name,
            "session_key":session_key.decode("utf-8"),
            "timestamp":timestamp
        }
        bob_encrypted_part=self.fernets["Bob"].encrypt(json.dumps(message_to_bob).encode("utf-8"))
        message={
            "message_to_alice":alice_encrypted_part,
            "message_to_bob":bob_encrypted_part,
            "bob_random_number":bob_random_number
        }
        event=Event(self,EventTypes.MFRT,message)
        self.send_down(event)

