from ahc.Ahc import *
from ahc.Channels.Channels import Channel
import networkx
import random
import hashlib
from time import  sleep

"""
    ************** Alice Class requirement *******************

    (1) Alice chooses a random number, x. 
        She computes y = f(x), where
        f(x) is the one-way function.

    (2) Alice sends y to Bob

    (4) If Bob’s guess is correct, the result of the coin flip is heads. If Bob’s
        guess is incorrect, the result of the coin flip is tails. Alice announces the
        result of the coin flip and sends x to Bob.
"""

randomInt_X=None

class Alice(ComponentModel):      

    def on_init(self, eventobj: Event):
        global randomInt_X
        randomInt_X=random.randint(0,999)
        
        print("\n*******  Alice is choosing a random number *******\n")
        print("Alice has chosen -> ",randomInt_X," (Bob can't see the chosen number)\n")
        print("Alice computes y = f(x)\n")
        hashed_Y=hashlib.sha256(str(randomInt_X).encode('ASCII')).hexdigest()
        print("y = ",hashed_Y)
        print("\n")
        header = GenericMessageHeader("Hash_header", 0, 1, interfaceid="0-1")
        message_alice = GenericMessage(header,hashed_Y)
        print("Alice is sending y to bob with message :",message_alice,"\n")
        event_alice=Event(self,EventTypes.MFRT,message_alice)
        self.send_down(event_alice)

    def on_message_from_bottom(self, eventobj: Event): # gets message 
        if eventobj.eventcontent.header.messagetype == "even_or_odd_header":
            #get bob's guess and check correct or not
            self.guessed_message = eventobj.eventcontent.payload
            print("Alice got the Bob's guessed message which is ",self.guessed_message)
            print("\n")
            # if bob's guess correct coin flip is HEAD
            if (randomInt_X%2 == 0 and self.guessed_message=="even") or (randomInt_X%2 == 1 and self.guessed_message=="odd"):

                print("******* Coin Fliping result is 'HEAD' ******\n")
                print("******* Bob guessed correctly ********\n")
                header=GenericMessageHeader("coin_flipped_header",0,1,interfaceid="0-1")
                message_alice=GenericMessage(header,randomInt_X)
                print("Alice is sending random x value message=  ", message_alice)
                print("\n")
                event_alice=Event(self,EventTypes.MFRT,message_alice)
                self.send_down(event_alice)

            else: # Guess is incorrect it means coin flip is TAIL
                print("******* Coin Fliping result is 'TAIL' ******\n")
                print("******* Bob guessed wrong ********\n")
                header=GenericMessageHeader("coin_flipped_header",0,1,interfaceid="0-1")
                message_alice=GenericMessage(header,randomInt_X)
                print("Alice is sending random x value message=  ", message_alice)
                print("\n")
                event_alice=Event(self,EventTypes.MFRT,message_alice)
                self.send_down(event_alice)   
        
        

"""
    ************** Bob Class requirement *******************

    (3) Bob guesses whether x is even or odd and sends his guess to Alice.

    (5) Bob confirms that y = f(x).

"""

hashvalue_y=None
class Bob(ComponentModel):

    def on_message_from_bottom(self, eventobj: Event):

        if eventobj.eventcontent.header.messagetype == "Hash_header":

            self.hashed_message = eventobj.eventcontent.payload
            global hashvalue_y
            hashvalue_y=self.hashed_message

            print("Bob got the y value from Alice which is ",hashvalue_y)
            print("\n")

            #guess whether x even or odd
            print("*******  Bob is guessing the whether x is even or odd *******\n")

            bob_guess=input("Guess x 'even' or 'odd': ")
            #get the hashed message y
            print("\n")
            
            header = GenericMessageHeader("even_or_odd_header", 1, 0, interfaceid="0-1")
            message_bob = GenericMessage(header,bob_guess)
            print("Bob is sending his guess message : ",message_bob)
            print("\n")
            event_bob=Event(self,EventTypes.MFRT,message_bob)
            self.send_down(event_bob)

        elif eventobj.eventcontent.header.messagetype == "coin_flipped_header":
            
            self.x_value = eventobj.eventcontent.payload
            print("Bob get the x value from Alice which is ", self.x_value)
            print("\n")
            hashed_Y=hashlib.sha256(str(self.x_value).encode('ASCII')).hexdigest()
            if hashed_Y==hashvalue_y:
                print("Bob confirmed the y = f(x) ")
            else:
                print("Bob could not confirm the y=f(x)")    

    def on_message_from_top(self, eventobj: Event):

        if eventobj.eventcontent.header.messagetype == "Hash_header":

            self.hashed_message = eventobj.eventcontent.payload
            global hashvalue_y
            hashvalue_y=self.hashed_message

            print("Bob got the y value from Alice which is ",hashvalue_y)
            print("\n")

            #guess whether x even or odd
            print("*******  Bob is guessing the whether x is even or odd *******\n")

            bob_guess=input("Guess x 'even' or 'odd': ")
            #get the hashed message y
            print("\n")
            
            header = GenericMessageHeader("even_or_odd_header", 1, 0, interfaceid="0-1")
            message_bob = GenericMessage(header,bob_guess)
            print("Bob is sending his guess message : ",message_bob)
            print("\n")
            event_bob=Event(self,EventTypes.MFRT,message_bob)
            self.send_down(event_bob)

        elif eventobj.eventcontent.header.messagetype == "coin_flipped_header":
            
            self.x_value = eventobj.eventcontent.payload
            print("Bob get the x value from Alice which is ", self.x_value)
            hashed_Y=hashlib.sha256(str(self.x_value).encode('ASCII')).hexdigest()
            if hashed_Y==hashvalue_y:
                print("Bob confirmed the y = f(x)...\n")
            else:
                print("Bob could not confirm the y=f(x) !!!!\n") 

           
def setup_topology():
    topology = Topology()
    channel = Channel("Channel", "0-1")
    sender = Alice("Alice", 0)
    receiver = Bob("Bob", 1)
    graph = networkx.Graph()
    topology.G = graph
    sender.connect_me_to_channel(ConnectorTypes.DOWN, channel)
    receiver.connect_me_to_channel(ConnectorTypes.DOWN, channel)
    topology.start()


def main():
    print("\n\n**********************************************")
    print("****                                          ****")
    print("****   Welcome To Explanation of              ****")
    print("****       Fair Coin Flipping                 ****")
    print("****         using One-Way function (sha256)  ****")
    print("****                                          ****")
    print("**************************************************\n\n")
    setup_topology()
    sleep(15)

if __name__ == "__main__":
    main()       