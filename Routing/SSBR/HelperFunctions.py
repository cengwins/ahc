import time
from Ahc import GenericMessage, GenericMessageHeader


def messageParser(self, eventobj):
    messagePayload = eventobj.eventcontent.payload
    messageFrom = eventobj.eventcontent.header.messagefrom
    
    print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")
    

    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), "-" + str(self.componentinstancenumber), interfaceid=str(self.componentinstancenumber))



    print(message_header)
    print("\n\n\n\n\n")
    message = GenericMessage(message_header, messagePayload)
    return message
        
        
def messageGenerator(self):
    time.sleep(1)
    message_payload = input("Enter message payload content...\n")

    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), "-" + str(self.componentinstancenumber), interfaceid=str(self.componentinstancenumber))
    message = GenericMessage(message_header, message_payload)

    print(f"{self.componentname}-{self.componentid} is generating a test message with content of \"{message_payload}\" in 3 seconds...\n")
    time.sleep(3)
    
    return message