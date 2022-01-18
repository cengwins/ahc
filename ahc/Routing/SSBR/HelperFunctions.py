import networkx as nx
from ahc.Ahc import GenericMessage, GenericMessageHeader, ComponentRegistry, Topology

def messageParser(self, eventobj, destination = ""):
    messageTo = eventobj.eventcontent.header.messageto
    if destination != "":
        messageTo = destination
    messagePayload = eventobj.eventcontent.payload
    messageFrom = eventobj.eventcontent.header.messagefrom
    #print(f"{self.componentname}-{self.componentid} got a message from {messageFrom}. \n Message is {messagePayload}\n")
    nextHop=eventobj.eventcontent.header.nexthop

    if eventobj.eventcontent.header.messagetype == "ROUTESEARCH":
        nextHop = None
    messageHeader = GenericMessageHeader(eventobj.eventcontent.header.messagetype, eventobj.eventcontent.header.messagefrom, messageTo, interfaceid = eventobj.eventcontent.header.interfaceid, nexthop=nextHop, sequencenumber = eventobj.eventcontent.header.sequencenumber)
    message = GenericMessage(messageHeader, messagePayload)
    
    return message
           
def buildRoutingTable(sourceNode, target):
    myNode = ComponentRegistry().get_component_by_key("FP", sourceNode)
    myNode.build_routing_table(target)

def benchmarkTest(nodeCount):
    myNode = ComponentRegistry().get_component_by_key("FP", 0)
    myNode.build_routing_table(nodeCount, 1, nodeCount)

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

        nodeToEditSST = ComponentRegistry().get_component_by_key("DRP",nodeToBeCalculated)
        
        for (key) in strongLinks.keys():
            nodeToEditSST.editSignalStabilityTable(key, "SC")
        for (key) in allNeighbors.keys():
            nodeToEditSST.editSignalStabilityTable(key, "WC")
    
    return
    
def printSSTInfo(nodeCount):
    for x in range(nodeCount):
        print("--------------------")
        print(f"Information of {x}:\n")
        nodeToEditSST = ComponentRegistry().get_component_by_key("DRP",x)
        print("Stability Table:")
        nodeToEditSST.printSignalStabilityTable()
        print("Routing Table:")
        nodeToEditSST = ComponentRegistry().get_component_by_key("FP",x)
        print(nodeToEditSST.routingTable)
        
def resetRoutingState(nodeCount):
    for x in range (0, nodeCount):
        nodeToEdit = ComponentRegistry().get_component_by_key("DRP",x)
        nodeToEditTwo = ComponentRegistry().get_component_by_key("SSBRNode",x)
        nodeToEditThree = ComponentRegistry().get_component_by_key("FP",x)
        nodeToEdit.routingTableFlag = False
        nodeToEditTwo.messageFrom = -1
        nodeToEditThree.node = 0
        nodeToEditThree.nodeCount = 0

def constructStrongRoute(graph, source, target):
    paths = nx.all_simple_paths(graph, source, target)
    sortedPath = sorted(paths, key=len)
    for i in sortedPath:
        desiredPath = True
        for index, item in enumerate(i):
            if len(i) > index+1:
                nodeToBeInvestigated = ComponentRegistry().get_component_by_key("DRP",i[index+1])
                if nodeToBeInvestigated.getSignalStabilityTable()[i[index]] == "WC":
                    desiredPath = False
        if desiredPath:
            return i
    return []
  
def SSBRRouteSearchMessage(self, target):
    message_payload = []
    messageFrom = str(self.componentname) + "-" + str(self.componentinstancenumber)
    messageTo = "FP" + "-" + str(target)
    message_header = GenericMessageHeader("ROUTESEARCH", messageFrom ,messageTo ,sequencenumber=0)
    message = GenericMessage(message_header, message_payload)

    return message

def SSBRRouteReplyMessage(self, eventobj):
    
    messagePayload = []
    messageFrom = eventobj.eventcontent.header.messagefrom
    messageTo = eventobj.eventcontent.header.messageto
    sequenceNumber = 0
    interfaceid = eventobj.eventcontent.header.interfaceid

    if int(self.componentinstancenumber) == int(interfaceid.split("-")[0]):
        nextHop = int(interfaceid.split("-")[1])
    else:
        nextHop = int(interfaceid.split("-")[0])
    
    messageHeader = GenericMessageHeader("ROUTEREPLY", messageTo, messageFrom, nextHop, interfaceid, sequenceNumber)
    message = GenericMessage(messageHeader, messagePayload)

    return message

def sendMessageToOtherNode(self, eventobj, nodeid):

    messageFrom = eventobj.eventcontent.header.messagefrom
    messageTo = eventobj.eventcontent.header.messageto
    if int(self.componentinstancenumber) > int(nodeid):
        interfaceid = str(nodeid)+"-"+str(self.componentinstancenumber)
    else:
        interfaceid=str(self.componentinstancenumber)+"-"+str(nodeid)

    sequenceNumber = int(eventobj.eventcontent.header.sequencenumber) + 1
    nextHop = nodeid
    messageType = eventobj.eventcontent.header.messagetype    
    messagePayload = eventobj.eventcontent.payload

    if eventobj.eventcontent.header.messagetype == "ROUTEREPLY":
        if int(eventobj.eventcontent.header.sequencenumber) == 0:
            messagePayload = []
        if self.componentinstancenumber not in messagePayload: messagePayload.append(self.componentinstancenumber)
        
    messageHeader = GenericMessageHeader(messageType, messageFrom, messageTo, nextHop, interfaceid, sequenceNumber)    
    message = GenericMessage(messageHeader, messagePayload)
    #print(messageHeader)
    #print(f"{nextHop} got a {eventobj.eventcontent.header.messagetype} message from {self.componentid}.\n")
    return message

def SSBRRouteCompletedMessage(self, eventobj):
    
    messagePayload = eventobj.eventcontent.payload
    messageFrom = eventobj.eventcontent.header.messagefrom
    messageTo = eventobj.eventcontent.header.messageto
    sequenceNumber = eventobj.eventcontent.header.sequencenumber
    interfaceid = eventobj.eventcontent.header.interfaceid
    nextHop = eventobj.eventcontent.header.nexthop
   
    messageHeader = GenericMessageHeader("ROUTECOMPLETED", messageTo, messageFrom, nextHop, interfaceid, sequenceNumber)
    message = GenericMessage(messageHeader, messagePayload)

    return message

def SSBRUnicastMessage(self, destination, message=""):
    messagePayload = message
    if (messagePayload == ""):
        messagePayload = input("Enter payload of message...\n")
    messageFrom = str(self.componentname) + "-" + str(self.componentid)
    messageTo = str(self.componentname) + "-" + str(destination)
    sequenceNumber = 0
   
    messageHeader = GenericMessageHeader("UNICASTDATA", messageFrom, messageTo, sequencenumber=sequenceNumber)
    message = GenericMessage(messageHeader, messagePayload)

    return message

def SSBRUnicastMessageFPParser(self, eventobj):
    target = eventobj.eventcontent.header.messageto.split("-")[1]
    nextHop = self.routingTable.get(str(target))
    messageHeader = GenericMessageHeader(eventobj.eventcontent.header.messagetype, eventobj.eventcontent.header.messagefrom, eventobj.eventcontent.header.messageto, nextHop, sequencenumber=eventobj.eventcontent.header.sequencenumber)
    message = GenericMessage(messageHeader, eventobj.eventcontent.payload)

    return message

    