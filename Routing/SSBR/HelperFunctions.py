import time
import networkx as nx
from Ahc import GenericMessage, GenericMessageHeader, ComponentRegistry

def convertTuple(tup):
    str = ''
    for item in tup:
        str = str + str(item)
    return str

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
    nodeToTest= input("Enter input node to sent message:\n")
    myNode = ComponentRegistry().get_component_by_key("ApplicationAndNetwork",nodeToTest)
    myNode.send_test_message()

def findStrongConnectedLinksForSingleNode(labels, threshold, nodeCount):

    for nodeToBeCalculated in range (nodeCount):
        
        strongLinks = dict()
        allNeighbors = dict()
        
        for (new_key, new_value) in labels.items():
        
            if new_value >= threshold:
                if (str(new_key[0]) == str(nodeToBeCalculated)):
                    strongLinks[new_key[1]] = new_value
                elif (str(new_key[1]) == str(nodeToBeCalculated)):
                    strongLinks[new_key[0]] = new_value
            elif (str(new_key[0]) == str(nodeToBeCalculated)):
                    allNeighbors[new_key[1]] = new_value
            elif (str(new_key[1]) == str(nodeToBeCalculated)):
                allNeighbors[new_key[0]] = new_value

        print(strongLinks)
        print(allNeighbors)
        nodeToEditSST = ComponentRegistry().get_component_by_key("DRP",nodeToBeCalculated)
        
        for (key) in strongLinks.keys():
            nodeToEditSST.editSignalStabilityTable(key, "SC")
        for (key) in allNeighbors.keys():
            nodeToEditSST.editSignalStabilityTable(key, "WC")
    
    return
    
def findAllSimplePaths(graph): 
    source = int(input("Enter source node id:\n"))
    target = int(input("Enter target node id:\n"))
    paths = nx.all_simple_paths(graph, source, target)
    sortedPath = sorted(paths, key=len)
    print(f"Possible paths between node#{source} to node#{target}")
    print(list(sortedPath))
    return sortedPath

def printSSTForANode():
    nodeId = int(input("Enter node to check its SC links... \n"))
    nodeToEditSST = ComponentRegistry().get_component_by_key("DRP",nodeId)
    nodeToEditSST.printSignalStabilityTable()
#def ApplicationAndNetworkComponentMessageHandler(self, eventobj):

