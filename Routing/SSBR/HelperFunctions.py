import time
from Ahc import GenericMessage, GenericMessageHeader, ComponentRegistry


def messageParser(self, eventobj):
    messagePayload = eventobj.eventcontent.payload
    messageFrom = eventobj.eventcontent.header.messagefrom
    print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")
    
    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), str(self.componentname)  + "-" + str(self.componentinstancenumber))
    message = GenericMessage(message_header, messagePayload)
    return message
           
def messageGenerator(self):
    time.sleep(1)
    message_payload = input("Enter message payload content...\n")

    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), str(self.componentname)  + "-" + str(self.componentinstancenumber), interfaceid=str(self.componentinstancenumber))
    message = GenericMessage(message_header, message_payload)

    print(f"{self.componentname}-{self.componentid} is generating a test message with content of \"{message_payload}\" in 3 seconds...\n")
    time.sleep(3)
    
    return message

def getMessageFromOtherNode(self, eventobj ,nodeid):

    interfaceid=str(self.componentinstancenumber)+"-"+str(nodeid)
    if nodeid < self.componentinstancenumber:
        interfaceid = str(nodeid)+"-"+str(self.componentinstancenumber)

    messagePayload = eventobj.eventcontent.payload

    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), str(self.componentname)  + "-" + str(nodeid), interfaceid=interfaceid)
    
    message = GenericMessage(message_header, messagePayload)

    print(f"{self.componentname}-{self.nodeid} got a message from {self.componentname}-{self.componentid}. \n Message is {messagePayload}\n")

    return message

def sendMessageToOtherNode(self, eventobj ,nodeid):

    messageFrom = eventobj.eventcontent.header.messagefrom
    interfaceid=str(self.componentinstancenumber)+"-"+str(nodeid)
    if nodeid < self.componentinstancenumber:
        interfaceid = str(nodeid)+"-"+str(self.componentinstancenumber)

    messagePayload = eventobj.eventcontent.payload

    message_header = GenericMessageHeader("SSBR", str(self.componentname) + "-" + str(self.componentinstancenumber), str(self.componentname)  + "-" + str(nodeid), interfaceid=interfaceid)
    
    message = GenericMessage(message_header, messagePayload)
    
    print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")

    return message

def triggerTestMessage():
    nodeToTest= input("Enter input node to sent message\n")
    myNode = ComponentRegistry().get_component_by_key("ApplicationAndNetwork",nodeToTest)
    myNode.trial()

#def ApplicationAndNetworkComponentMessageHandler(self, eventobj):
