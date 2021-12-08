import time


def messageParser(self, eventobj):
    messageFrom = eventobj.eventcontent["from"]
    message = eventobj.eventcontent["message"]
    
    print(f"{self.componentname} - #{self.componentid} got a message from {messageFrom}. \n Message is {message}\n")
    eventMessage = {
        "from": "{} - #{}".format(self.componentname,self.componentid),
        "message": message,
    } 
    return eventMessage
        
def messageGenerator(self):
    time.sleep(1)
    testMessage = input("Enter message text content...\n")
    print(f"{self.componentname} - #{self.componentid} is generating a test message with content of \"{testMessage}\" in 3 seconds...")
    time.sleep(3)
    
    eventMessage = {
        "from": "{} - #{}".format(self.componentname,self.componentid),
        "message": testMessage,
    }

    return eventMessage