from enum import Enum
from ahc.Ahc import GenericMessageHeader

class AODVMessageTypes(Enum):
    RREQ = "RREQ"
    RREP = "RREP"
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"

class AODVMessageHeader(GenericMessageHeader):
    _broadcastid = 1

    def __init__(self, messagetype, messagefrom, messageto, hopcount, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=1):
        super().__init__(messagetype,messagefrom, messageto, nexthop, interfaceid, sequencenumber)
        self.hopcount = hopcount
        self.broadcastid = AODVMessageHeader._broadcastid
        AODVMessageHeader._broadcastid += 1
        
        

        

